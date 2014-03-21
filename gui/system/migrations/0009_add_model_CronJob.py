# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'CronJob'
        db.create_table('system_cronjob', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cron_minute', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('cron_hour', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('cron_daymonth', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('cron_month', self.gf('django.db.models.fields.CharField')(default='1,2,3,4,5,6,7,8,9,10,a,b,c', max_length=100)),
            ('cron_dayweek', self.gf('django.db.models.fields.CharField')(default='1,2,3,4,5,6,7', max_length=100)),
            ('cron_user', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('cron_command', self.gf('django.db.models.fields.CharField')(max_length=120)),
        ))
        db.send_create_signal('system', ['CronJob'])


    def backwards(self, orm):
        
        # Deleting model 'CronJob'
        db.delete_table('system_cronjob')


    models = {
        'system.advanced': {
            'Meta': {'object_name': 'Advanced'},
            'adv_consolemenu': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adv_consolemsg': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'adv_consolescreensaver': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adv_firmwarevc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adv_motd': ('django.db.models.fields.TextField', [], {'max_length': '1024'}),
            'adv_powerdaemon': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adv_serialconsole': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adv_swapondrive': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'adv_systembeep': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adv_traceback': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adv_tuning': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'adv_zeroconfbonjour': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'system.cronjob': {
            'Meta': {'object_name': 'CronJob'},
            'cron_command': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'cron_daymonth': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'cron_dayweek': ('django.db.models.fields.CharField', [], {'default': "'1,2,3,4,5,6,7'", 'max_length': '100'}),
            'cron_hour': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'cron_minute': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'cron_month': ('django.db.models.fields.CharField', [], {'default': "'1,2,3,4,5,6,7,8,9,10,a,b,c'", 'max_length': '100'}),
            'cron_user': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'system.email': {
            'Meta': {'object_name': 'Email'},
            'em_fromemail': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'em_outgoingserver': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'em_pass': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'em_port': ('django.db.models.fields.IntegerField', [], {'default': '25'}),
            'em_security': ('django.db.models.fields.CharField', [], {'default': "'plain'", 'max_length': '120'}),
            'em_smtp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'em_user': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'system.rsync': {
            'Meta': {'object_name': 'Rsync'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rsync_archive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rsync_compress': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rsync_daymonth': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'rsync_dayweek': ('django.db.models.fields.CharField', [], {'default': "'1,2,3,4,5,6,7'", 'max_length': '100'}),
            'rsync_delete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rsync_desc': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'rsync_extra': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'rsync_hour': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'rsync_minute': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'rsync_month': ('django.db.models.fields.CharField', [], {'default': "'1,2,3,4,5,6,7,8,9,10,a,b,c'", 'max_length': '100'}),
            'rsync_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'rsync_preserveattr': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rsync_preserveperm': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rsync_quiet': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rsync_recursive': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rsync_remotehost': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'rsync_remotemodule': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'rsync_times': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rsync_user': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'system.settings': {
            'Meta': {'object_name': 'Settings'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stg_guiprotocol': ('django.db.models.fields.CharField', [], {'default': "'http'", 'max_length': '120'}),
            'stg_language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '120'}),
            'stg_ntpserver1': ('django.db.models.fields.CharField', [], {'default': "'0.freebsd.pool.ntp.org iburst maxpoll 9'", 'max_length': '120'}),
            'stg_ntpserver2': ('django.db.models.fields.CharField', [], {'default': "'1.freebsd.pool.ntp.org iburst maxpoll 9'", 'max_length': '120', 'blank': 'True'}),
            'stg_ntpserver3': ('django.db.models.fields.CharField', [], {'default': "'2.freebsd.pool.ntp.org iburst maxpoll 9'", 'max_length': '120', 'blank': 'True'}),
            'stg_timezone': ('django.db.models.fields.CharField', [], {'default': "'America/Los_Angeles'", 'max_length': '120'})
        },
        'system.ssl': {
            'Meta': {'object_name': 'SSL'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ssl_certfile': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'ssl_city': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'ssl_common': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'ssl_country': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'ssl_email': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'ssl_org': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'ssl_state': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'ssl_unit': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['system']
