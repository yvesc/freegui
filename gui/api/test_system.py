# Make sure to load all modules
from django.db.models.loading import cache
cache.get_apps()

from freenasUI.api.tests.utils import APITestCase
from freenasUI.storage.models import Disk, MountPoint, Volume
from freenasUI.system import models


class CronJobResourceTest(APITestCase):

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
            data={
                'cron_user': 'root',
                'cron_command': 'ls /',
                'cron_minute': '*/20',
                'cron_hour': '*',
                'cron_daymonth': '*',
                'cron_month': '*',
                'cron_dayweek': '*',
            }
        )
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': 1,
            u'cron_command': u'ls /',
            u'cron_daymonth': u'*',
            u'cron_dayweek': u'*',
            u'cron_description': u'',
            u'cron_enabled': True,
            u'cron_hour': u'*',
            u'cron_minute': u'*/20',
            u'cron_month': u'*',
            u'cron_stderr': False,
            u'cron_stdout': True,
            u'cron_user': u'root',
        })

    def test_Retrieve(self):
        obj = models.CronJob.objects.create(
            cron_user='root',
            cron_command='ls /',
        )
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, [{
            u'id': obj.id,
            u'cron_command': u'ls /',
            u'cron_daymonth': u'*',
            u'cron_dayweek': u'*',
            u'cron_description': u'',
            u'cron_enabled': True,
            u'cron_hour': u'*',
            u'cron_minute': u'00',
            u'cron_month': u'*',
            u'cron_stderr': False,
            u'cron_stdout': True,
            u'cron_user': u'root',
        }])

    def test_Update(self):
        obj = models.CronJob.objects.create(
            cron_user='root',
            cron_command='ls /',
            cron_dayweek='*',
            cron_stdout=True,
        )
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
            data={
                'cron_dayweek': '1,2',
                'cron_stdout': False,
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], obj.id)
        self.assertEqual(data['cron_dayweek'], '1,2')
        self.assertEqual(data['cron_stdout'], False)

    def test_Delete(self):
        obj = models.CronJob.objects.create(
            cron_user='root',
            cron_command='ls /',
            cron_dayweek='*',
            cron_stdout=True,
        )
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
        )
        self.assertHttpAccepted(resp)


class InitShutdownResourceTest(APITestCase):

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
            data={
                'ini_type': 'command',
                'ini_command': 'echo "init" > /tmp/init',
                'ini_when': 'postinit',
            }
        )
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': 1,
            u'ini_command': u'echo "init" > /tmp/init',
            u'ini_script': None,
            u'ini_type': u'command',
            u'ini_when': u'postinit'
        })

    def test_Retrieve(self):
        obj = models.InitShutdown.objects.create(
            ini_type='command',
            ini_command='echo "init" > /tmp/init',
            ini_when='postinit',
        )
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, [{
            u'id': obj.id,
            u'ini_command': u'echo "init" > /tmp/init',
            u'ini_script': None,
            u'ini_type': u'command',
            u'ini_when': u'postinit'
        }])

    def test_Update(self):
        obj = models.InitShutdown.objects.create(
            ini_type='command',
            ini_command='echo "init" > /tmp/init',
            ini_when='postinit',
        )
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
            data={
                'ini_when': 'preinit',
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], obj.id)
        self.assertEqual(data['ini_when'], 'preinit')

    def test_Delete(self):
        obj = models.InitShutdown.objects.create(
            ini_type='command',
            ini_command='echo "init" > /tmp/init',
            ini_when='postinit',
        )
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
        )
        self.assertHttpAccepted(resp)


class NTPServerResourceTest(APITestCase):

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
            data={
                'ntp_address': '0.freebsd.pool.ntp.org',
            }
        )
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': 1,
            u'ntp_address': u'0.freebsd.pool.ntp.org',
            u'ntp_burst': False,
            u'ntp_iburst': True,
            u'ntp_maxpoll': 10,
            u'ntp_minpoll': 6,
            u'ntp_prefer': False
        })

    def test_Retrieve(self):
        obj = models.NTPServer.objects.create(
            ntp_address='0.freebsd.pool.ntp.org',
        )
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, [{
            u'id': obj.id,
            u'ntp_address': u'0.freebsd.pool.ntp.org',
            u'ntp_burst': False,
            u'ntp_iburst': True,
            u'ntp_maxpoll': 10,
            u'ntp_minpoll': 6,
            u'ntp_prefer': False
        }])

    def test_Update(self):
        obj = models.NTPServer.objects.create(
            ntp_address='0.freebsd.pool.ntp.org',
            ntp_prefer=False,
        )
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
            data={
                'ntp_prefer': True,
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], obj.id)
        self.assertEqual(data['ntp_prefer'], True)

    def test_Delete(self):
        obj = models.NTPServer.objects.create(
            ntp_address='0.freebsd.pool.ntp.org',
        )
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
        )
        self.assertHttpAccepted(resp)


class RsyncResourceTest(APITestCase):

    def setUp(self):
        super(RsyncResourceTest, self).setUp()
        v = Volume.objects.create(
            vol_name='tank',
            vol_fstype='ZFS',
        )
        MountPoint.objects.create(
            mp_path='/mnt/tank',
            mp_volume=v,
        )

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
            data={
                'rsync_path': '/mnt/tank',
                'rsync_user': 'root',
                'rsync_mode': 'module',
                'rsync_remotemodule': 'testmodule',
                'rsync_remotehost': 'testhost',
                'rsync_direction': 'push',
                'rsync_minute': '*/20',
                'rsync_hour': '*',
                'rsync_daymonth': '*',
                'rsync_month': '*',
                'rsync_dayweek': '*',
            }
        )
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': 1,
            u'rsync_archive': False,
            u'rsync_compress': True,
            u'rsync_daymonth': u'*',
            u'rsync_dayweek': u'*',
            u'rsync_delete': False,
            u'rsync_desc': u'',
            u'rsync_direction': u'push',
            u'rsync_enabled': True,
            u'rsync_extra': u'',
            u'rsync_hour': u'*',
            u'rsync_minute': u'*/20',
            u'rsync_mode': u'module',
            u'rsync_month': u'*',
            u'rsync_path': u'/mnt/tank',
            u'rsync_preserveattr': False,
            u'rsync_preserveperm': False,
            u'rsync_quiet': False,
            u'rsync_recursive': True,
            u'rsync_remotehost': u'testhost',
            u'rsync_remotemodule': u'testmodule',
            u'rsync_remotepath': u'',
            u'rsync_remoteport': 22,
            u'rsync_times': True,
            u'rsync_user': u'root'
        })

    def test_Retrieve(self):
        obj = models.Rsync.objects.create(
            rsync_path='/mnt',
            rsync_user='root',
        )
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, [{
            u'id': obj.id,
            u'rsync_archive': False,
            u'rsync_compress': True,
            u'rsync_daymonth': u'*',
            u'rsync_dayweek': u'*',
            u'rsync_delete': False,
            u'rsync_desc': u'',
            u'rsync_direction': u'push',
            u'rsync_enabled': True,
            u'rsync_extra': u'',
            u'rsync_hour': u'*',
            u'rsync_minute': u'00',
            u'rsync_mode': u'module',
            u'rsync_month': u'*',
            u'rsync_path': u'/mnt',
            u'rsync_preserveattr': False,
            u'rsync_preserveperm': False,
            u'rsync_quiet': False,
            u'rsync_recursive': True,
            u'rsync_remotehost': u'',
            u'rsync_remotemodule': u'',
            u'rsync_remotepath': u'',
            u'rsync_remoteport': 22,
            u'rsync_times': True,
            u'rsync_user': u'root'
        }])

    def test_Update(self):
        obj = models.Rsync.objects.create(
            rsync_path='/mnt/tank',
            rsync_user='root',
            rsync_recursive=True,
            rsync_remotehost='testhost',
            rsync_remotemodule='testmodule',
        )
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
            data={
                'rsync_recursive': False,
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], obj.id)
        self.assertEqual(data['rsync_recursive'], False)

    def test_Delete(self):
        obj = models.Rsync.objects.create(
            rsync_path='/mnt/tank',
            rsync_user='root',
        )
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
        )
        self.assertHttpAccepted(resp)


class SMARTTestResourceTest(APITestCase):

    def setUp(self):
        super(SMARTTestResourceTest, self).setUp()
        self._disk1 = Disk.objects.create(
            disk_name='ada1',
        )
        self._disk2 = Disk.objects.create(
            disk_name='ada2',
        )

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
            data={
                'smarttest_disks': [self._disk1.id, self._disk2.id],
                'smarttest_type': 'L',
                'smarttest_hour': '*',
                'smarttest_daymonth': '*',
                'smarttest_month': '*',
                'smarttest_dayweek': '*',
            }
        )
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': 1,
            u'smarttest_daymonth': u'*',
            u'smarttest_dayweek': u'*',
            u'smarttest_desc': u'',
            u'smarttest_disks': [1, 2],
            u'smarttest_hour': u'*',
            u'smarttest_month': u'*',
            u'smarttest_type': u'L'
        })

    def test_Retrieve(self):
        obj = models.SMARTTest.objects.create(
            smarttest_type='L',
        )
        obj.smarttest_disks.add(self._disk1)
        obj.smarttest_disks.add(self._disk2)
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, [{
            u'id': obj.id,
            u'smarttest_daymonth': u'*',
            u'smarttest_dayweek': u'*',
            u'smarttest_desc': u'',
            u'smarttest_disks': [1, 2],
            u'smarttest_hour': u'*',
            u'smarttest_month': u'*',
            u'smarttest_type': u'L'
        }])

    def test_Update(self):
        obj = models.SMARTTest.objects.create(
            smarttest_type='L',
        )
        obj.smarttest_disks.add(self._disk1)
        obj.smarttest_disks.add(self._disk2)
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
            data={
                'smarttest_type': 'S',
                'smarttest_disks': [self._disk1.id, self._disk2.id],  #FIXME
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], obj.id)
        self.assertEqual(data['smarttest_type'], 'S')

    def test_Delete(self):
        obj = models.SMARTTest.objects.create(
            smarttest_type='L',
        )
        obj.smarttest_disks.add(self._disk1)
        obj.smarttest_disks.add(self._disk2)
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
        )
        self.assertHttpAccepted(resp)


class SysctlResourceTest(APITestCase):

    def setUp(self):
        super(SysctlResourceTest, self).setUp()

    def tearDown(self):
        super(SysctlResourceTest, self).tearDown()

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create_sysctl(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
            data={
                'sysctl_mib': 'kern.coredump',
                'sysctl_enabled': True,
                'sysctl_value': '1',
            }
        )
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': 1,
            u'sysctl_comment': u'',
            u'sysctl_enabled': True,
            u'sysctl_mib': u'kern.coredump',
            u'sysctl_value': u'1',
        })

    def test_Retrieve_sysctl(self):
        sysctl = models.Sysctl.objects.create(
            sysctl_mib='kern.coredump',
            sysctl_value='2',
        )
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, [
            {
                u'id': sysctl.id,
                u'sysctl_comment': sysctl.sysctl_comment,
                u'sysctl_enabled': sysctl.sysctl_enabled,
                u'sysctl_mib': sysctl.sysctl_mib,
                u'sysctl_value': sysctl.sysctl_value,
            }
        ])

    def test_Update_sysctl(self):
        sysctl = models.Sysctl.objects.create(
            sysctl_mib='kern.coredump',
            sysctl_value='1',
        )
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), sysctl.id),
            format='json',
            data={
                'sysctl_value': '2',
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], sysctl.id)
        self.assertEqual(data['sysctl_value'], '2')

    def test_Delete_sysctl(self):
        sysctl = models.Sysctl.objects.create(
            sysctl_mib='kern.coredump',
            sysctl_value='1',
        )
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), sysctl.id),
            format='json',
        )
        self.assertHttpAccepted(resp)


class TunableResourceTest(APITestCase):

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
            data={
                'tun_var': 'xhci_load',
                'tun_value': 'YES',
            }
        )
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': 1,
            u'tun_comment': u'',
            u'tun_enabled': True,
            u'tun_value': u'YES',
            u'tun_var': u'xhci_load'
        })

    def test_Retrieve(self):
        obj = models.Tunable.objects.create(
            tun_var='xhci_load',
            tun_value='YES',
        )
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, [{
            u'id': obj.id,
            u'tun_comment': u'',
            u'tun_enabled': True,
            u'tun_value': u'YES',
            u'tun_var': u'xhci_load'
        }])

    def test_Update(self):
        obj = models.Tunable.objects.create(
            tun_var='xhci_load',
            tun_value='YES',
            tun_enabled=True
        )
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
            data={
                'tun_enabled': False,
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], obj.id)
        self.assertEqual(data['tun_enabled'], False)

    def test_Delete(self):
        obj = models.Tunable.objects.create(
            tun_var='xhci_load',
            tun_value='YES',
        )
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), obj.id),
            format='json',
        )
        self.assertHttpAccepted(resp)


class SettingsResourceTest(APITestCase):

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpMethodNotAllowed(resp)

    def test_Retrieve(self):
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': self._settings.id,
            u'stg_directoryservice': u'',
            u'stg_guiaddress': u'0.0.0.0',
            u'stg_guihttpsport': None,
            u'stg_guiport': None,
            u'stg_guiprotocol': u'http',
            u'stg_guiv6address': u'::',
            u'stg_kbdmap': u'',
            u'stg_language': u'en',
            u'stg_syslogserver': u'',
            u'stg_timezone': u'America/Los_Angeles'
        })

    def test_Update(self):
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), self._settings.id),
            format='json',
            data={
                'stg_timezone': 'America/Sao_Paulo',
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], self._settings.id)
        self.assertEqual(data['stg_timezone'], 'America/Sao_Paulo')

    def test_Delete(self):
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), 1),
            format='json',
        )
        self.assertHttpMethodNotAllowed(resp)


class AdvancedResourceTest(APITestCase):

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpMethodNotAllowed(resp)

    def test_Retrieve(self):
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': self._advanced.id,
            u'adv_advancedmode': False,
            u'adv_anonstats': True,
            u'adv_anonstats_token': u'',
            u'adv_autotune': False,
            u'adv_consolemenu': False,
            u'adv_consolemsg': True,
            u'adv_consolescreensaver': False,
            u'adv_debugkernel': False,
            u'adv_motd': u'Welcome',
            u'adv_powerdaemon': False,
            u'adv_serialconsole': False,
            u'adv_serialport': u'0x2f8',
            u'adv_serialspeed': u'9600',
            u'adv_swapondrive': 2,
            u'adv_traceback': True,
            u'adv_uploadcrash': True,
        })

    def test_Update(self):
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), self._advanced.id),
            format='json',
            data={
                'adv_powerdaemon': True,
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], self._advanced.id)
        self.assertEqual(data['adv_powerdaemon'], True)

    def test_Delete(self):
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), 1),
            format='json',
        )
        self.assertHttpMethodNotAllowed(resp)


class EmailResourceTest(APITestCase):

    def setUp(self):
        super(EmailResourceTest, self).setUp()
        self._obj = models.Email.objects.create()

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(
            self.client.get(self.get_api_url(), format='json')
        )

    def test_Create(self):
        resp = self.api_client.post(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpMethodNotAllowed(resp)

    def test_Retrieve(self):
        resp = self.api_client.get(
            self.get_api_url(),
            format='json',
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data, {
            u'id': self._obj.id,
            u'em_fromemail': u'',
            u'em_outgoingserver': u'',
            u'em_pass': None,
            u'em_port': 25,
            u'em_security': u'plain',
            u'em_smtp': False,
            u'em_user': None,
        })

    def test_Update(self):
        resp = self.api_client.put(
            '%s%d/' % (self.get_api_url(), self._obj.id),
            format='json',
            data={
                'em_fromemail': 'dev@ixsystems.com',
                'em_outgoingserver': 'mail.ixsystems.com',
            }
        )
        self.assertHttpOK(resp)
        data = self.deserialize(resp)
        self.assertEqual(data['id'], self._advanced.id)
        self.assertEqual(data['em_fromemail'], 'dev@ixsystems.com')
        self.assertEqual(data['em_outgoingserver'], 'mail.ixsystems.com')

    def test_Delete(self):
        resp = self.api_client.delete(
            '%s%d/' % (self.get_api_url(), 1),
            format='json',
        )
        self.assertHttpMethodNotAllowed(resp)
