import subprocess

from django.utils.translation import ugettext as _

from freenasUI.system.alert import alertPlugins, Alert, BaseAlert
from freenasUI.storage.models import Volume


class ZpoolCapAlert(BaseAlert):

    def run(self):
        alerts = []
        for vol in Volume.objects.filter(vol_fstype='ZFS'):
            proc = subprocess.Popen([
                "/sbin/zpool",
                "list",
                "-H",
                vol.vol_name.encode('utf8'),
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            data = proc.communicate()[0]
            if proc.returncode != 0:
                continue
            cap = int(data.split('\t')[4].replace('%', ''))
            msg = _(
                'The capacity for the volume \'%s\' is currently at %d%%, '
                'while the recommended value is below 80%%.'
            )
            level = None
            if cap >= 90:
                level = Alert.CRIT
            elif cap >= 80:
                level = Alert.WARN
            if level:
                alerts.append(
                    Alert(
                        level,
                        msg % (vol.vol_name, cap),
                    )
                )
        return alerts

alertPlugins.register(ZpoolCapAlert)
