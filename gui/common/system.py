#+
# Copyright 2010 iXsystems, Inc.
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#####################################################################

import logging
import os
import re
import smtplib
import sqlite3
import subprocess
import sys
import syslog
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.Utils import formatdate
from datetime import datetime, timedelta

from django.utils.translation import ugettext_lazy as _

RE_MOUNT = re.compile(
    r'^(?P<fs_spec>.+?) on (?P<fs_file>.+?) \((?P<fs_vfstype>\w+)', re.S
)
VERSION_FILE = '/etc/version'
_VERSION = None
log = logging.getLogger("common.system")


def get_sw_version(strip_build_num=False):
    """Return the full version string, e.g. FreeNAS-8.1-r7794-amd64."""

    global _VERSION

    if _VERSION is None:
        with open(VERSION_FILE) as fd:
            _VERSION = fd.read().strip()
    if strip_build_num:
        return _VERSION.split(' ')[0]
    return _VERSION


def get_sw_login_version():
    """Return a shortened version string, e.g. 8.0.1-RC1, 8.1, etc. """

    return '-'.join(get_sw_version(strip_build_num=True).split('-')[1:-2])


def get_sw_name():
    """Return the software name, e.g. FreeNAS"""

    return get_sw_version().split('-')[0]


def get_freenas_var_by_file(f, var):
    assert f and var

    pipe = os.popen('. "%s"; echo "${%s}"' % (f, var, ))
    try:
        val = pipe.readlines()[-1].rstrip()
    finally:
        pipe.close()

    return val


def get_freenas_var(var, default=None):
    val = get_freenas_var_by_file("/etc/rc.freenas", var)
    if not val:
        val = default
    return val

FREENAS_DATABASE = get_freenas_var("FREENAS_DATABASE", "/data/freenas-v1.db")


def send_mail(subject=None,
              text=None,
              interval=timedelta(),
              channel=None,
              to=None,
              extra_headers=None,
              attachments=None,
              ):
    from freenasUI.account.models import bsdUsers
    from freenasUI.network.models import GlobalConfiguration
    from freenasUI.system.models import Email
    if not channel:
        channel = get_sw_name().lower()
    if interval > timedelta():
        channelfile = '/tmp/.msg.%s' % (channel)
        last_update = datetime.now() - interval
        try:
            last_update = datetime.fromtimestamp(os.stat(channelfile).st_mtime)
        except OSError:
            pass
        timediff = datetime.now() - last_update
        if (timediff >= interval) or (timediff < timedelta()):
            open(channelfile, 'w').close()
        else:
            return True, 'This message was already sent in the given interval'

    error = False
    errmsg = ''
    em = Email.objects.all().order_by('-id')[0]
    if not to:
        to = [bsdUsers.objects.get(bsdusr_username='root').bsdusr_email]
    if attachments:
        msg = MIMEMultipart()
        msg.preamble = text
        map(lambda attachment: msg.attach(attachment), attachments)
    else:
        msg = MIMEText(text, _charset='utf-8')
    if subject:
        msg['Subject'] = subject
    msg['From'] = em.em_fromemail
    msg['To'] = ', '.join(to)
    msg['Date'] = formatdate()

    if not extra_headers:
        extra_headers = {}
    for key, val in extra_headers.items():
        if key in msg:
            msg.replace_header(key, val)
        else:
            msg[key] = val
    msg = msg.as_string()

    try:
        gc = GlobalConfiguration.objects.order_by('-id')[0]
        local_hostname = "%s.%s" % (gc.gc_hostname, gc.gc_domain)
    except:
        local_hostname = None

    try:
        if not em.em_outgoingserver or not em.em_port:
            # See NOTE below.
            raise ValueError('you must provide an outgoing mailserver and mail'
                             ' server port when sending mail')
        if em.em_security == 'ssl':
            server = smtplib.SMTP_SSL(
                em.em_outgoingserver,
                em.em_port,
                timeout=10,
                local_hostname=local_hostname)
        else:
            server = smtplib.SMTP(
                em.em_outgoingserver,
                em.em_port,
                timeout=10,
                local_hostname=local_hostname)
            if em.em_security == 'tls':
                server.starttls()
        if em.em_smtp:
            server.login(
                em.em_user.encode('utf-8'),
                em.em_pass.encode('utf-8'))
        # NOTE: Don't do this.
        #
        # If smtplib.SMTP* tells you to run connect() first, it's because the
        # mailserver it tried connecting to via the outgoing server argument
        # was unreachable and it tried to connect to 'localhost' and barfed.
        # This is because FreeNAS doesn't run a full MTA.
        #else:
        #    server.connect()
        server.sendmail(em.em_fromemail, to, msg)
        server.quit()
    except ValueError, ve:
        # Don't spam syslog with these messages. They should only end up in the
        # test-email pane.
        errmsg = str(ve)
        error = True
    except Exception, e:
        syslog.openlog(channel, syslog.LOG_CONS | syslog.LOG_PID,
                       facility=syslog.LOG_MAIL)
        try:
            for line in traceback.format_exc().splitlines():
                syslog.syslog(syslog.LOG_ERR, line)
        finally:
            syslog.closelog()
        errmsg = str(e)
        error = True
    return error, errmsg


def get_fstype(path):
    assert path

    if not os.access(path, os.F_OK):
        return None

    lines = subprocess.check_output(['/bin/df', '-T', path]).splitlines()

    out = (lines[len(lines) - 1]).split()

    return (out[1].upper())


def get_mounted_filesystems():
    """Return a list of dict with info of mounted file systems

    Each dict is composed of:
        - fs_spec (src)
        - fs_file (dest)
        - fs_vfstype
    """
    mounted = []

    lines = subprocess.check_output(['/sbin/mount']).splitlines()

    for line in lines:
        reg = RE_MOUNT.search(line)
        if not reg:
            continue
        mounted.append(reg.groupdict())

    return mounted


def is_mounted(**kwargs):

    mounted = get_mounted_filesystems()
    for mountpt in mounted:
        ret = False
        if 'device' in kwargs:
            ret = True if mountpt['fs_spec'] == kwargs['device'] else False
        if 'path' in kwargs:
            ret = True if mountpt['fs_file'] == kwargs['path'] else False
        if ret:
            break

    return ret


def mount(dev, path, mntopts=None, fstype=None):
    if isinstance(dev, unicode):
        dev = dev.encode('utf-8')

    if isinstance(path, unicode):
        path = path.encode('utf-8')

    if mntopts:
        opts = ['-o', mntopts]
    else:
        opts = []

    fstype = ['-t', fstype] if fstype else []

    proc = subprocess.Popen(
        ['/sbin/mount'] + opts + fstype + [dev, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    output = proc.communicate()[0]

    if proc.returncode != 0:
        log.debug("Mount failed (%s): %s", proc.returncode, output)
        raise ValueError(_(
            "Mount failed (%(retcode)s) -> %(output)s" % {
                'retcode': proc.returncode,
                'output': output,
            }
        ))
    else:
        return True


def umount(path):

    proc = subprocess.Popen(
        ['/sbin/umount', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    output = proc.communicate()[0]

    if proc.returncode != 0:
        log.debug("Umount failed (%s): %s", proc.returncode, output)
        return False
    else:
        return True


def service_enabled(name):
    db = get_freenas_var("FREENAS_DATABASE", "/data/freenas-v1.db")
    h = sqlite3.connect(db)
    c = h.cursor()

    enabled = False
    sql = "select srv_enable from services_services " \
        "where srv_service = '%s' order by -id limit 1" % name
    c.execute(sql)
    row = c.fetchone()
    if row and row[0] != 0:
        enabled = True

    c.close()
    h.close()

    return enabled


def get_directoryservice():
    directoryservice = None

    db = get_freenas_var("FREENAS_DATABASE", "/data/freenas-v1.db")
    h = sqlite3.connect(db)
    c = h.cursor()

    sql = "select stg_directoryservice from system_settings"
    c.execute(sql)
    row = c.fetchone()
    if row and row[0]:
        directoryservice = row[0]

    c.close()
    h.close()

    return directoryservice


def ldap_enabled():
    enabled = False

    if (
        service_enabled('directoryservice') and
        get_directoryservice() == 'ldap'
    ):
        enabled = True

    return enabled


def ldap_objects():
    h = sqlite3.connect(FREENAS_DATABASE)
    h.row_factory = sqlite3.Row
    c = h.cursor()

    results = c.execute("SELECT * FROM services_ldap ORDER BY -id")

    objects = []
    for row in results:
        obj = {}
        for key in row.keys():
            obj[key] = row[key]
        objects.append(obj)

    c.close()
    h.close()
    return objects


def activedirectory_enabled():
    enabled = False

    if (
        service_enabled('directoryservice') and
        get_directoryservice() == 'activedirectory'
    ):
        enabled = True

    return enabled


def activedirectory_objects():
    h = sqlite3.connect(FREENAS_DATABASE)
    h.row_factory = sqlite3.Row
    c = h.cursor()

    results = c.execute("SELECT * FROM services_activedirectory ORDER BY -id")

    objects = []
    for row in results:
        obj = {}
        for key in row.keys():
            obj[key] = row[key]
        objects.append(obj)

    c.close()
    h.close()
    return objects


def domaincontroller_enabled():
    enabled = False

    if (
        service_enabled('directoryservice') and
        get_directoryservice() == 'domaincontroller'
    ):
        enabled = True

    return enabled


def domaincontroller_objects():
    h = sqlite3.connect(FREENAS_DATABASE)
    h.row_factory = sqlite3.Row
    c = h.cursor()

    results = c.execute("SELECT * FROM services_domaincontroller ORDER BY -id")

    objects = []
    for row in results:
        obj = {}
        for key in row.keys():
            obj[key] = row[key]
        objects.append(obj)

    c.close()
    h.close()
    return objects


def nt4_enabled():
    enabled = False

    if (
        service_enabled('directoryservice') and
        get_directoryservice() == 'nt4'
    ):
        enabled = True

    return enabled


def nt4_objects():
    h = sqlite3.connect(FREENAS_DATABASE)
    h.row_factory = sqlite3.Row
    c = h.cursor()

    results = c.execute("SELECT * FROM services_nt4 ORDER BY -id")

    objects = []
    for row in results:
        obj = {}
        for key in row.keys():
            obj[key] = row[key]
        objects.append(obj)

    c.close()
    h.close()
    return objects


def nis_enabled():
    enabled = False

    if (
        service_enabled('directoryservice') and
        get_directoryservice() == 'nis'
    ):
        enabled = True

    return enabled


def nis_objects():
    h = sqlite3.connect(FREENAS_DATABASE)
    h.row_factory = sqlite3.Row
    c = h.cursor()

    results = c.execute("SELECT * FROM services_nis ORDER BY -id")

    objects = []
    for row in results:
        obj = {}
        for key in row.keys():
            obj[key] = row[key]
        objects.append(obj)

    c.close()
    h.close()
    return objects


def get_avatar_conf():
    avatar_conf = {}
    avatar_vars = [
        'AVATAR_PROJECT',
        'AVATAR_PROJECT_SITE',
        'AVATAR_SUPPORT_SITE',
        'AVATAR_VERSION',
        'AVATAR_BUILD_NUMBER',
        'AVATAR_ARCH',
        'AVATAR_COMPONENT',
    ]

    for av in avatar_vars:
        avatar_conf[av] = get_freenas_var_by_file("/etc/avatar.conf", av)

    return avatar_conf


def get_system_dataset():
    from freenasUI.storage.models import Volume
    from freenasUI.system.models import Advanced

    try:
        adv = Advanced.objects.all()[0]
    except:
        log.error("No advanced settings!")
        return None, None

    system_pool = adv.adv_system_pool
    if not system_pool:
        log.error("No system pool configured!")
        return None, None

    volume = Volume.objects.filter(vol_name=system_pool)
    if not volume:
        log.error("You need to create a volume to proceed!")
        return None, None

    volume = volume[0]
    basename = "%s/.system" % volume.vol_name
    return volume, basename


def get_samba4_path():
    """
    Returns the volume and path for the samba4 storage path
    """
    from freenasUI.storage.models import Volume
    from freenasUI.system.models import Advanced

    try:
        adv = Advanced.objects.all()[0]
    except Exception:
        print >> sys.stderr, "No advanced settings!"
        sys.exit(1)

    system_pool = adv.adv_system_pool
    if not system_pool:
        print >> sys.stderr, "No system pool configured!"
        sys.exit(1)

    volume = Volume.objects.filter(vol_name=system_pool)
    if not volume:
        print >> sys.stderr, "You need to create a volume to proceed!"
        sys.exit(1)

    volume = volume[0]
    basename = "%s/.system/samba4" % volume.vol_name
    return volume, basename


def exclude_path(path, exclude):

    if isinstance(path, unicode):
        path = path.encode('utf8')

    exclude = map(
        lambda y: y.encode('utf8') if isinstance(y, unicode) else y,
        exclude
    )

    fine_grained = []
    for e in exclude:
        if not e.startswith(path):
            continue
        fine_grained.append(e)

    if fine_grained:
        apply_paths = []
        check_paths = [os.path.join(path, f) for f in os.listdir(path)]
        while check_paths:
            fpath = check_paths.pop()
            if not os.path.isdir(fpath):
                apply_paths.append(fpath)
                continue
            for fg in fine_grained:
                if fg.startswith(fpath):
                    if fg != fpath:
                        check_paths.extend([
                            os.path.join(fpath, f)
                            for f in os.listdir(fpath)
                        ])
                else:
                    apply_paths.append(fpath)
        return apply_paths
    else:
        return [path]
