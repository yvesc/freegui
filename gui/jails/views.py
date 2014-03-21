#+
# Copyright 2013 iXsystems, Inc.
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
import json
import logging
import os
import string
import time

from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _

from freenasUI.freeadmin.views import JsonResp
from freenasUI.jails import forms, models
from freenasUI.jails.utils import get_jails_index
from freenasUI.common.warden import (
    Warden,
    WARDEN_EXPORT_FLAGS_DIR
)
from freenasUI.middleware.exceptions import MiddlewareError
from freenasUI.middleware.notifier import notifier

log = logging.getLogger("jails.views")


def jails_home(request):
    default_iface = notifier().guess_default_interface()

    try:
        jailsconf = models.JailsConfiguration.objects.order_by("-id")[0]

    except IndexError:
        jailsconf = models.JailsConfiguration.objects.create()

    if not jailsconf.jc_collectionurl:
        jailsconf.jc_collectionurl = get_jails_index()
        jailsconf.save()

    return render(request, 'jails/index.html', {
        'focus_form': request.GET.get('tab', 'jails.View'),
        'jailsconf': jailsconf,
        'default_iface': default_iface
    })


def jailsconfiguration(request):

    try:
        jailsconf = models.JailsConfiguration.objects.order_by("-id")[0]

    except IndexError:
        jailsconf = models.JailsConfiguration.objects.create()

    return render(request, 'jails/index.html', {
        'focus_form': request.GET.get('tab', 'jails.JailsConfiguration.View'),
        'jailsconf': jailsconf
    })


def jail_edit(request, id):

    jail = models.Jails.objects.get(id=id)

    if request.method == 'POST':
        form = forms.JailsEditForm(request.POST, instance=jail)
        if form.is_valid():
            form.save()
            return JsonResp(
                request,
                message=_("Jail successfully edited.")
            )
    else:
        form = forms.JailsEditForm(instance=jail)

    return render(request, 'jails/edit.html', {
        'form': form
    })


def jail_storage_add(request, jail_id):

    jail = models.Jails.objects.get(id=jail_id)

    if request.method == 'POST':
        form = forms.NullMountPointForm(request.POST, jail=jail)
        if form.is_valid():
            form.save()
            return JsonResp(
                request,
                message=_("Storage successfully added.")
            )
    else:
        form = forms.NullMountPointForm(jail=jail)

    return render(request, 'jails/storage.html', {
        'form': form,
    })


def jail_start(request, id):

    jail = models.Jails.objects.get(id=id)

    if request.method == 'POST':
        try:
            notifier().reload("http")  # Jail IP reflects nginx plugins.conf
            Warden().start(jail=jail.jail_host)
            return JsonResp(
                request,
                message=_("Jail successfully started.")
            )

        except Exception, e:
            return JsonResp(request, error=True, message=repr(e))

    else:
        return render(request, "jails/start.html", {
            'name': jail.jail_host
        })


def jail_stop(request, id):

    jail = models.Jails.objects.get(id=id)

    if request.method == 'POST':
        try:
            Warden().stop(jail=jail.jail_host)
            return JsonResp(
                request,
                message=_("Jail successfully stopped.")
            )

        except Exception, e:
            return JsonResp(request, error=True, message=repr(e))

    else:
        return render(request, "jails/stop.html", {
            'name': jail.jail_host
        })


def jail_delete(request, id):

    jail = models.Jails.objects.get(id=id)

    if request.method == 'POST':
        try:
            jail.delete()
            return JsonResp(
                request,
                message=_("Jail successfully deleted.")
            )
        except MiddlewareError:
            raise
        except Exception, e:
            return JsonResp(request, error=True, message=repr(e))

    else:
        return render(request, "jails/delete.html", {
            'name': jail.jail_host
        })


def jail_export(request, id):

    jail = models.Jails.objects.get(id=id)
    jailsconf = models.JailsConfiguration.objects.order_by("-id")[0]

    dir = jailsconf.jc_path
    filename = "%s/%s.wdn" % (dir, jail.jail_host)

    Warden().export(
        jail=jail.jail_host, path=dir, flags=WARDEN_EXPORT_FLAGS_DIR
    )

    freenas_build = "UNKNOWN"
    #FIXME
    """
    try:
        with open(VERSION_FILE) as d:
            freenas_build = d.read().strip()
    except:
        pass
    """

    wrapper = FileWrapper(file(filename))
    response = HttpResponse(wrapper, content_type='application/octet-stream')
    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = \
        'attachment; filename=%s-%s-%s.wdn' % (
            jail.jail_host.encode('utf-8'),
            freenas_build,
            time.strftime('%Y%m%d%H%M%S'))

    return response

jail_progress_estimated_time = 600
jail_progress_start_time = 0
jail_progress_percent = 0


def jail_progress(request):
    global jail_progress_estimated_time
    global jail_progress_start_time
    global jail_progress_percent

    data = {
        'size': 0,
        'data': '',
        'state': 'running',
        'eta': 0,
        'percent': 0
    }

    logfile = '/var/tmp/warden.log'
    if os.path.exists(logfile):
        f = open(logfile, "r")
        buf = f.readlines()
        f.close()

        percent = 0
        size = len(buf)
        if size > 0:
            for line in buf:
                if line.startswith('====='):
                    parts = line.split()
                    if len(parts) > 1:
                        percent = parts[1][:-1]

            buf = string.join(buf)
            size = len(buf)

        if not percent:
            percent = 0

        elapsed = 1
        curtime = int(time.time())

        if jail_progress_start_time == 0:
            jail_progress_start_time = curtime
            eta = jail_progress_estimated_time

        else:
            elapsed = curtime - jail_progress_start_time
            eta = jail_progress_estimated_time - elapsed

        if percent > 0 and jail_progress_percent != percent:
            p = float(percent) / 100
            #t = float(p) * jail_progress_estimated_time

            estimated_time = elapsed / p
            eta = estimated_time - elapsed

            jail_progress_estimated_time = estimated_time

        if eta > 3600:
            data['eta'] = "%02d:%02d:%02d" % (eta / 3600, eta / 60, eta % 60)
        elif eta > 0:
            data['eta'] = "%02d:%02d" % (eta / 60, eta % 60)
        else:
            data['eta'] = "00:00"

        data['percent'] = percent
        data['size'] = size
        data['data'] = buf

        jail_progress_percent = percent

        if not os.path.exists("/var/tmp/.jailcreate"):
            data['state'] = 'done'
            jail_progress_estimated_time = 600
            jail_progress_start_time = 0
            jail_progress_percent = 0

    return HttpResponse(json.dumps(data), content_type="application/json")

linux_jail_progress_estimated_time = 600
linux_jail_progress_start_time = 0
linux_jail_progress_percent = 0

#
# XXX HACK XXX
#
# This is just another progress view! We need a univeral means to do this!
#
# XXX HACK XXX
#
def jail_linuxprogress(request):
    global linux_jail_progress_estimated_time
    global linux_jail_progress_start_time
    global linux_jail_progress_percent

    data = {
        'size': 0,
        'data': '',
        'state': 'running',
        'eta': 0,
        'percent': 0
    }

    statusfile = os.environ['EXTRACT_TARBALL_STATUSFILE']
    if os.path.exists("/var/tmp/.templatecreate") and os.path.exists(statusfile):
        percent = 0

        try:
            f = open(statusfile, "r")
            buf = f.readlines()[-1].strip()
            f.close()

            parts = buf.split()
            size = len(parts)
            if size > 2:
                nbytes = float(parts[1])
                total = float(parts[2])
                percent = int((nbytes / total) * 100)
        except:
            pass

        if not percent:
            percent = 0

        elapsed = 1
        curtime = int(time.time())

        if linux_jail_progress_start_time == 0:
            linux_jail_progress_start_time = curtime
            eta = linux_jail_progress_estimated_time

        else:
            elapsed = curtime - linux_jail_progress_start_time
            eta = linux_jail_progress_estimated_time - elapsed

        if percent > 0 and linux_jail_progress_percent != percent:
            p = float(percent) / 100
            #t = float(p) * linux_jail_progress_estimated_time

            estimated_time = elapsed / p
            eta = estimated_time - elapsed

            linux_jail_progress_estimated_time = estimated_time

        if eta > 3600:
            data['eta'] = "%02d:%02d:%02d" % (eta / 3600, eta / 60, eta % 60)
        elif eta > 0:
            data['eta'] = "%02d:%02d" % (eta / 60, eta % 60)
        else:
            data['eta'] = "00:00"

        data['percent'] = percent
        data['size'] = size
        data['data'] = buf

        linux_jail_progress_percent = percent

        if not os.path.exists("/var/tmp/.templatecreate"):
            data['state'] = 'done'
            linux_jail_progress_estimated_time = 600
            linux_jail_progress_start_time = 0
            linux_jail_progress_percent = 0

    return HttpResponse(json.dumps(data), content_type="application/json")

def jail_template_edit(request, id):

    jt = models.JailTemplate.objects.get(id=id)

    if request.method == 'POST':
        form = forms.JailTemplateEditForm(request.POST, instance=jt)
        if form.is_valid():
            form.save()
            return JsonResp(
                request,
                message=_("Jail template successfully edited.")
            )
    else:
        form = forms.JailTemplateEditForm(instance=jt)

    return render(request, 'jails/template_edit.html', {
        'form': form
    })

def jail_import(request):
    log.debug("XXX: jail_import()")
    return render(request, 'jails/import.html', {})


def jail_auto(request, id):
    log.debug("XXX: jail_auto()")
    return render(request, 'jails/auto.html', {})


def jail_checkup(request, id):
    log.debug("XXX: jail_checkup()")
    return render(request, 'jails/checkup.html', {})


def jail_details(request, id):
    log.debug("XXX: jail_details()")
    return render(request, 'jails/details.html', {})


def jail_options(request, id):
    log.debug("XXX: jail_options()")
    return render(request, 'jails/options.html', {})


def jail_pkgs(request, id):
    log.debug("XXX: jail_pkgs()")
    return render(request, 'jails/pkgs.html', {})


def jail_pbis(request, id):
    log.debug("XXX: jail_pbis()")
    return render(request, 'jails/pbis.html', {})


def jail_zfsmksnap(request, id):
    log.debug("XXX: jail_zfsmksnap()")
    return render(request, 'jails/zfsmksnap.html', {})


def jail_zfslistclone(request, id):
    log.debug("XXX: jail_zfslistclone()")
    return render(request, 'jails/zfslistclone.html', {})


def jail_zfslistsnap(request, id):
    log.debug("XXX: jail_zfslistsnap()")
    return render(request, 'jails/zfslistsnap.html', {})


def jail_zfsclonesnap(request, id):
    log.debug("XXX: jail_zfsclonesnap()")
    return render(request, 'jails/zfsclonesnap.html', {})


def jail_zfscronsnap(request, id):
    log.debug("XXX: jail_zfscronsnap()")
    return render(request, 'jails/zfscronsnap.html', {})


def jail_zfsrevertsnap(request, id):
    log.debug("XXX: jail_zfsrevertsnap()")
    return render(request, 'jails/zfsrevertsnap.html', {})


def jail_zfsrmclonesnap(request, id):
    log.debug("XXX: jail_zfsrmclonesnap()")
    return render(request, 'jails/zfsrmclonesnap.html', {})


def jail_zfsrmsnap(request, id):
    log.debug("XXX: jail_zfsrmsnap()")
    return render(request, 'jails/zfsrmsnap.html', {})


def jail_template_info(request, name):

    data = { }
    jt = models.JailTemplate.objects.get(jt_name=name)
    if jt:
        data['jt_name'] = jt.jt_name
        data['jt_os'] = jt.jt_os
        data['jt_arch'] = jt.jt_arch
        data['jt_url'] = jt.jt_url

    content = json.dumps(data)
    return HttpResponse(content, content_type='application/json')
