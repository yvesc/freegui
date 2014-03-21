#+
# Copyright 2011 iXsystems, Inc.
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
import os
import logging
import platform

from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _

from freenasUI.common.jail import Jls
from freenasUI.common.pbi import pbi_delete
from freenasUI.freeadmin.models import Model
from freenasUI.jails.models import Jails, JailsConfiguration
from freenasUI.middleware.exceptions import MiddlewareError
from freenasUI.middleware.notifier import notifier

log = logging.getLogger('plugins.models')


class Plugins(Model):
    plugin_name = models.CharField(
        max_length=120,
        verbose_name=_("Plugin name"),
        help_text=_("Name of the plugin")
        )

    plugin_pbiname = models.CharField(
        max_length=120,
        verbose_name=_("Plugin info name"),
        help_text=_("Info name of the plugin")
        )

    plugin_version = models.CharField(
        max_length=120,
        verbose_name=_("Plugin version"),
        help_text=_("Version of the plugin")
        )

    plugin_api_version = models.CharField(
        max_length=20,
        default="1",
        verbose_name=_("Plugin API version"),
        )

    plugin_arch = models.CharField(
        max_length=120,
        verbose_name=_("Plugin architecture"),
        help_text=_("Plugin architecture")
        )

    plugin_enabled = models.BooleanField(
        verbose_name=_("Plugin enabled"),
        help_text=_("Plugin enabled"),
        default=False
        )

    plugin_ip = models.IPAddressField(
        max_length=120,
        verbose_name=_("Plugin IP address"),
        help_text=_("Plugin IP address")
        )

    plugin_port = models.IntegerField(
        max_length=120,
        verbose_name=_("Plugin TCP port"),
        help_text=_("Plugin TCP port"),
        )

    plugin_path = models.CharField(
        max_length=1024,
        verbose_name=_("Plugin archive path"),
        help_text=_("Path where the plugins are saved after installation")
        )

    plugin_jail = models.CharField(
        max_length=120,
        verbose_name=_("Plugin jail name"),
        help_text=_("Jail where the plugin is installed")
        )

    plugin_secret = models.ForeignKey(
        'services.RPCToken',
        on_delete=models.PROTECT,  # Do not allow foreign key to be deleted
        )

    class Meta:
        verbose_name = _(u"Plugin")
        verbose_name_plural = _(u"Plugins")

    def _do_delete(self):
        jc = JailsConfiguration.objects.order_by('-id')[0]
        pbi_path = os.path.join(
            jc.jc_path,
            self.plugin_jail,
            "usr/pbi",
            "%s-%s" % (self.plugin_name, platform.machine()),
        )
        jail = None
        for j in Jls():
            if j.hostname == self.plugin_jail:
                jail = j
                break
        if jail is None:
            raise MiddlewareError(_(
                "The plugins jail is not running, start it before proceeding"
            ))

        notifier().umount_filesystems_within(pbi_path)
        p = pbi_delete(pbi=self.plugin_pbiname)
        res = p.run(jail=True, jid=jail.jid)
        if not res or res[0] != 0:
            log.warn("unable to delete %s", self.plugin_pbiname)

    def delete(self, *args, **kwargs):
        qs = Plugins.objects.filter(plugin_jail=self.plugin_jail).exclude(
            id__exact=self.id
        )
        with transaction.atomic():
            jc = JailsConfiguration.objects.order_by('-id')[0]
            jaildir = "%s/%s" % (jc.jc_path, self.plugin_jail)

            notifier()._stop_plugins(
                jail=self.plugin_jail,
                plugin=self.plugin_name,
            )
            if qs.count() > 0:
                self._do_delete()
            else:
                self._do_delete()
                if os.path.exists("%s/.plugins/PLUGIN" % jaildir):
                    try:
                        jail = Jails.objects.get(jail_host=self.plugin_jail)
                        jail.delete(force=True)
                    except Jails.DoesNotExist:
                        pass
            super(Plugins, self).delete(*args, **kwargs)
            self.plugin_secret.delete()


class Kmod(Model):

    plugin = models.ForeignKey(
        Plugins,
        editable=False,
    )
    module = models.CharField(
        max_length=400,
    )
    within_pbi = models.BooleanField(
        default=False,
    )
    order = models.IntegerField(
        default=1,
    )

    class Meta:
        verbose_name = _("Plugin Kernel Module")

    def __unicode__(self):
        return u'%s (%s)' % (self.module, self.plugin.plugin_name)

    def save(self, *args, **kwargs):
        if self.order is None:
            self.order = Kmod.objects.filter(plugin=self.plugin).count() + 1
        super(Kmod, self).save(*args, **kwargs)


class Available(models.Model):

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=200,
    )

    description = models.CharField(
        verbose_name=_("Description"),
        max_length=200,
    )

    version = models.CharField(
        verbose_name=_("Version"),
        max_length=200,
    )

    class Meta:
        abstract = True


class Configuration(Model):

    repourl = models.CharField(
        verbose_name=_("Repository URL"),
        max_length=255,
        help_text=_("URL for the plugins repository"),
        blank=True,
    )

    class FreeAdmin:
        deletable = False

    class Meta:
        verbose_name = _("Configuration")
