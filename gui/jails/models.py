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
import glob
import logging
import os
import re

from django.db import models
from django.utils.translation import ugettext_lazy as _

from freenasUI import choices
from freenasUI.common.pipesubr import pipeopen
from freenasUI.common.sipcalc import sipcalc_type
from freenasUI.common.system import is_mounted, mount, umount
from freenasUI.common.warden import (
    Warden,
    WARDEN_AUTOSTART_ENABLED, WARDEN_AUTOSTART_DISABLED,
    WARDEN_VNET_ENABLED, WARDEN_VNET_DISABLED,
    WARDEN_NAT_ENABLED, WARDEN_NAT_DISABLED,
    WARDEN_DELETE_FLAGS_CONFIRM,
    WARDEN_TEMPLATE_FLAGS_DELETE
)
from freenasUI.freeadmin.models import Model, Network4Field, Network6Field
from freenasUI.jails.queryset import JailsQuerySet
from freenasUI.middleware.exceptions import MiddlewareError
from freenasUI.middleware.notifier import notifier

log = logging.getLogger('jails.models')


class JailsManager(models.Manager):
    use_for_related_fields = True

    def __init__(self, qs_class=models.query.QuerySet):
        self.queryset_class = qs_class
        super(JailsManager, self).__init__()

    def get_queryset(self):
        return JailsQuerySet(self.model)

    def __getattr__(self, name):
        return getattr(self.get_queryset(), name)


class Jails(Model):
    objects = JailsManager()

    jail_host = models.CharField(
        max_length=120,
        verbose_name=_("Jail Name"),
    )
    jail_type = models.CharField(
        max_length=120,
        verbose_name=_("Type")
    )
    jail_ipv4 = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv4 address")
    )
    jail_ipv4_netmask = models.CharField(
        max_length=3,
        choices=choices.v4NetmaskBitList,
        blank=True,
        default='',
        verbose_name=_("IPv4 netmask"),
    )
    jail_alias_ipv4 = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv4 aliases")
    )
    jail_bridge_ipv4 = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv4 bridge address")
    )
    jail_bridge_ipv4_netmask = models.CharField(
        max_length=3,
        choices=choices.v4NetmaskBitList,
        blank=True,
        default='',
        verbose_name=_("IPv4 bridge netmask"),
    )
    jail_alias_bridge_ipv4 = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv4 bridge aliases")
    )
    jail_defaultrouter_ipv4 = models.IPAddressField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv4 default gateway")
    )
    jail_ipv6 = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv6 address")
    )
    jail_ipv6_prefix = models.CharField(
        max_length=4,
        choices=choices.v6NetmaskBitList,
        blank=True,
        default='',
        verbose_name=_("IPv6 prefix length")
    )
    jail_alias_ipv6 = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv6 aliases")
    )
    jail_bridge_ipv6 = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv6 bridge address")
    )
    jail_bridge_ipv6_prefix = models.CharField(
        max_length=4,
        choices=choices.v6NetmaskBitList,
        blank=True,
        default='',
        verbose_name=_("IPv6 bridge prefix length")
    )
    jail_alias_bridge_ipv6 = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("IPv6 bridge aliases")
    )
    jail_defaultrouter_ipv6 = models.GenericIPAddressField(
        max_length=120,
        blank=True,
        null=True,
        protocol='IPv6',
        verbose_name=_("IPv6 default gateway")
    )
    jail_mac = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name=_("MAC")
    )
    jail_flags = models.TextField(
        verbose_name=_("Sysctls"),
        blank=True,
        help_text=_("Comma delimited list of sysctl's")
    )
    jail_autostart = models.BooleanField(
        max_length=120,
        default=True,
        verbose_name=_("Autostart")
    )
    jail_status = models.CharField(
        max_length=120,
        verbose_name=_("Status")
    )
    jail_vnet = models.BooleanField(
        max_length=120,
        default=True,
        verbose_name=_("VIMAGE")
    )
    jail_nat = models.BooleanField(
        default=False,
        verbose_name=_("NAT")
    )

    @property
    def jail_path(self):
        if self.__jail_path:
            return self.__jail_path
        else:
            try:
                jc = JailsConfiguration.objects.order_by("-id")[0] 
                self.__jail_path = "%s/%s" % (jc.jc_path, self.jail_host)
            except:
                pass

        return self.__jail_path

    @property
    def jail_meta_path(self):
        if self.__jail_meta_path:
            return self.__jail_meta_path
        else:
            try:
                jc = JailsConfiguration.objects.order_by("-id")[0] 
                self.__jail_meta_path = "%s/.%s.meta" % (jc.jc_path, self.jail_host)
            except:
                pass

        return self.__jail_meta_path

    def __str__(self):
        return str(self.jail_host)

    def __unicode__(self):
        return unicode(self.jail_host)

    def __init__(self, *args, **kwargs):
        super(Jails, self).__init__(*args, **kwargs)
        self.__jail_path = None
        self.__jail_meta_path = None

        if self.jail_autostart == WARDEN_AUTOSTART_ENABLED:
            self.jail_autostart = True
        elif self.jail_autostart == WARDEN_AUTOSTART_DISABLED:
            self.jail_autostart = False

        if self.jail_vnet == WARDEN_VNET_ENABLED:
            self.jail_vnet = True
        elif self.jail_vnet == WARDEN_VNET_DISABLED:
            self.jail_vnet = False

        if self.jail_nat == WARDEN_NAT_ENABLED:
            self.jail_nat = True
        elif self.jail_nat == WARDEN_NAT_DISABLED:
            self.jail_nat = False

        #
        # XXX
        #
        # This should probably be done in forms.py.. but for some reason,
        # probably related to how this model fakes out django and doesn't
        # use a database table (just a guess), when changing the form instance
        # variable, it does not reflect in the GUI. Will return to this 
        # particular issue some other time. For now, hacky hack hacks!
        #
        # Also note, the mask/prefix is stripped here for display in the GUI,
        # and appended back on in the form save() method.
        #
        # XXX
        #
        if self.jail_ipv4:
            parts = self.jail_ipv4.split('/')
            self.jail_ipv4 = parts[0]
            if len(parts) > 1:
                self.jail_ipv4_netmask = parts[1]

        if self.jail_bridge_ipv4:
            parts = self.jail_bridge_ipv4.split('/')
            self.jail_bridge_ipv4 = parts[0]
            if len(parts) > 1:
                self.jail_bridge_ipv4_netmask = parts[1]

        if self.jail_ipv6:
            parts = self.jail_ipv6.split('/')
            self.jail_ipv6 = parts[0]
            if len(parts) > 1:
                self.jail_ipv6_prefix = parts[1]

        if self.jail_bridge_ipv6:
            parts = self.jail_bridge_ipv6.split('/')
            self.jail_bridge_ipv6 = parts[0]
            if len(parts) > 1:
                self.jail_bridge_ipv6_prefix = parts[1]

    def delete(self, force=False):
        #FIXME: Cyclic dependency
        from freenasUI.plugins.models import Plugins
        if not force:
            qs = Plugins.objects.filter(plugin_jail=self.jail_host)
            if qs.exists():
                raise MiddlewareError(
                    _("This jail is required by %d plugin(s)") % qs.count()
                )
        Warden().delete(jail=self.jail_host, flags=WARDEN_DELETE_FLAGS_CONFIRM)

    def is_linux_jail(self):
        is_linux = False

        sysctl_path = "%s/sbin/sysctl" % (self.jail_path)
        p = pipeopen("file %s" % sysctl_path, important=False)
        out = p.communicate()
        if p.returncode != 0:
            return is_linux

        try:
            out = out[0]
            parts = out.split(',')
            line = parts[4]
            parts = line.split()
            line = parts[1] 
            if re.match('(.+)?linux(.+)?', line, flags=re.I):
                is_linux = True

        except:
            is_linux = False 

        return is_linux

    class Meta:
        verbose_name = _("Jails")
        verbose_name_plural = _("Jails")


class JailsConfiguration(Model):

    jc_path = models.CharField(
        max_length=1024,
        verbose_name=_("Jail Root"),
        help_text=_("Path where to store jail data")
    )
    jc_ipv4_network = Network4Field(
        blank=True,
        verbose_name=_("IPv4 Network"),
        help_text=_("IPv4 network range for jails and plugins"),
    )
    jc_ipv4_network_start = Network4Field(
        blank=True,
        verbose_name=_("IPv4 Network Start Address"),
        help_text=_("IPv4 network start address for jails and plugins"),
    )
    jc_ipv4_network_end = Network4Field(
        blank=True,
        verbose_name=_("IPv4 Network End Address"),
        help_text=_("IPv4 network end address for jails and plugins"),
    )
    jc_ipv6_network = Network6Field(
        blank=True,
        verbose_name=_("IPv6 Network"),
        help_text=_("IPv6 network range for jails and plugins")
    )
    jc_ipv6_network_start = Network6Field(
        blank=True,
        verbose_name=_("IPv6 Network Start Address"),
        help_text=_("IPv6 network start address for jails and plugins")
    )
    jc_ipv6_network_end = Network6Field(
        blank=True,
        verbose_name=_("IPv6 Network End Address"),
        help_text=_("IPv6 network end address for jails and plugins")
    )
    jc_collectionurl = models.CharField(
        verbose_name=_("Collection URL"),
        max_length=255,
        help_text=_("URL for the jails index"),
        blank=True,
    )

    def save(self, *args, **kwargs):
        super(JailsConfiguration, self).save(*args, **kwargs)
        notifier().start("ix-warden")

    class Meta:
        verbose_name = _("Jails Configuration")
        verbose_name_plural = _("Jails Configuration")

    class FreeAdmin:
        deletable = False

    def __init__(self, *args, **kwargs):
        super(JailsConfiguration, self).__init__(*args, **kwargs)
        iface = notifier().guess_default_interface()
        if not iface:
            return

        st = sipcalc_type(iface=iface)
        if not st:
            return

        if not st.is_ipv4():
            return

        if not self.jc_ipv4_network:
            self.jc_ipv4_network = "%s/%d" % (
                st.network_address, st.network_mask_bits
            )

        if not self.jc_ipv4_network_start:
            self.jc_ipv4_network_start = str(st.usable_range[0]).split('/')[0]
        else:
            self.jc_ipv4_network_start = self.jc_ipv4_network_start.split('/')[0]  

        if not self.jc_ipv4_network_end:
            self.jc_ipv4_network_end = str(st.usable_range[1]).split('/')[0]
        else:
            self.jc_ipv4_network_end = self.jc_ipv4_network_end.split('/')[0]


class JailTemplate(Model):

    jt_name = models.CharField(
        max_length=120,
        verbose_name=_("Name"),
        unique=True
    )

    jt_os = models.CharField(
        max_length=120,
        verbose_name=_("OS"),
        choices=choices.JAIL_TEMPLATE_OS_CHOICES
    )

    jt_arch = models.CharField(
        max_length=120,
        verbose_name=_("Architecture"),
        choices=choices.JAIL_TEMPLATE_ARCH_CHOICES
    )

    jt_url = models.CharField(
        max_length=255,
        verbose_name=_("URL")
    )

    @property
    def jt_instances(self):
        template = self.jt_name
        instances = 0

        jc = JailsConfiguration.objects.all()[0]
        if not jc:
            return 0

        tdir = os.path.realpath("%s/.warden-template-%s" % (jc.jc_path, template))
        if not os.path.exists(tdir):
            return 0

        p = pipeopen("/sbin/zfs list -H -o name %s" % tdir)
        zfsout = p.communicate()
        if p.returncode != 0:
            return 0
        if not zfsout:
            return 0

        template_dataset = zfsout[0].strip()
        for metadir in glob.iglob("%s/.*.meta" % jc.jc_path):
            metadir = metadir.split('/')[-1]
            jail = re.sub('\.meta|\.', '', metadir)
            rp = os.path.realpath("%s/%s" % (jc.jc_path, jail))

            p = pipeopen("/sbin/zfs get -H origin %s" % rp)
            zfsout = p.communicate()
            if p.returncode != 0:
                continue
            if not zfsout:
                continue

            zfsout = zfsout[0]
            parts = zfsout.split('\t')
            if len(parts) < 3:
                continue

            snapshot = parts[2].strip()
            dataset = snapshot.replace('@clean', '')
            if template_dataset == dataset:
                instances += 1

        return instances

    def delete(self, force=False):
        ninstances = self.jt_instances
        if ninstances != 0:
            raise MiddlewareError(
                _("Template must have 0 instances!")
            )

        template = self.jt_name
        jc = JailsConfiguration.objects.all()[0]
        if not jc:
            raise MiddlewareError(
                _("Jail root is not configured!")
            )

        tdir = os.path.realpath("%s/.warden-template-%s" % (jc.jc_path, template))
        if not os.path.exists(tdir):
            super(JailTemplate, self).delete()
            return

        try:
            w = Warden()
            template_delete_args = {}
            template_delete_args['flags'] = WARDEN_TEMPLATE_FLAGS_DELETE
            template_delete_args['template'] = self.jt_name
            w.template(**template_delete_args)
            super(JailTemplate, self).delete()

        except Exception as e:
            raise MiddlewareError(_(e))

    class Meta:
        verbose_name = _("Jail Templates")
        verbose_name_plural = _("Jail Templates")


class NullMountPoint(Model):

    jail = models.CharField(
        max_length=120,
        verbose_name=_("Jail"),
    )
    source = models.CharField(
        max_length=300,
        verbose_name=_("Source"),
    )
    destination = models.CharField(
        max_length=300,
        verbose_name=_("Destination"),
    )
    readonly = models.BooleanField(
        default=False,
        verbose_name=_("Read-Only"),
    )
    fstype = models.CharField(
        max_length=300,
        verbose_name=_("Filesystem"),
        choices=choices.NULLMOUNTPOINT_CHOICES,
        default='nullfs'
    ) 

    class Meta:
        verbose_name = _(u"Storage")
        verbose_name_plural = _(u"Storage")

    def __unicode__(self):
        return self.source

    def delete(self, *args, **kwargs):
        if self.mounted:
            self.umount()
        super(NullMountPoint, self).delete(*args, **kwargs)

    @property
    def mounted(self):
        return is_mounted(device=self.source, path=self.destination_jail)

    @property
    def destination_jail(self):
        jc = JailsConfiguration.objects.order_by("-id")[0]
        return u"%s/%s%s" % (jc.jc_path, self.jail, self.destination)

    def mount(self):
        mntopts = None
        if self.readonly:
            mntopts = 'ro'
        mount(
            self.source,
            self.destination_jail,
            fstype=self.fstype,  
            mntopts=mntopts,
        )
        return self.mounted

    def umount(self):
        umount(self.destination_jail)
        return not self.mounted
