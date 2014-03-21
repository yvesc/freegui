# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


class Migration(DataMigration):

    def forwards(self, orm):

        # Adding field 'NullMountPoint.readonly'
        db.add_column(u'jails_nullmountpoint', 'readonly',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


        # Changing field 'JailsConfiguration.jc_ipv6_network_start'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv6_network_start', self.gf('freenasUI.freeadmin.models.fields.Network6Field')(max_length=43))

        # Changing field 'JailsConfiguration.jc_ipv6_network'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv6_network', self.gf('freenasUI.freeadmin.models.fields.Network6Field')(max_length=43))

        # Changing field 'JailsConfiguration.jc_ipv6_network_end'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv6_network_end', self.gf('freenasUI.freeadmin.models.fields.Network6Field')(max_length=43))

        # Changing field 'JailsConfiguration.jc_ipv4_network'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv4_network', self.gf('freenasUI.freeadmin.models.fields.Network4Field')(max_length=18))

        # Changing field 'JailsConfiguration.jc_ipv4_network_start'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv4_network_start', self.gf('freenasUI.freeadmin.models.fields.Network4Field')(max_length=18))

        # Changing field 'JailsConfiguration.jc_ipv4_network_end'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv4_network_end', self.gf('freenasUI.freeadmin.models.fields.Network4Field')(max_length=18))

        # Workaround south bug
        orm['jails.NullMountPoint'].objects.update(
            readonly=False,
        )

    def backwards(self, orm):

        # Deleting field 'NullMountPoint.readonly'
        db.delete_column(u'jails_nullmountpoint', 'readonly')


        # Changing field 'JailsConfiguration.jc_ipv6_network_start'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv6_network_start', self.gf('freenasUI.freeadmin.models.Network6Field')(max_length=43))

        # Changing field 'JailsConfiguration.jc_ipv6_network'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv6_network', self.gf('freenasUI.freeadmin.models.Network6Field')(max_length=43))

        # Changing field 'JailsConfiguration.jc_ipv6_network_end'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv6_network_end', self.gf('freenasUI.freeadmin.models.Network6Field')(max_length=43))

        # Changing field 'JailsConfiguration.jc_ipv4_network'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv4_network', self.gf('freenasUI.freeadmin.models.Network4Field')(max_length=18))

        # Changing field 'JailsConfiguration.jc_ipv4_network_start'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv4_network_start', self.gf('freenasUI.freeadmin.models.Network4Field')(max_length=18))

        # Changing field 'JailsConfiguration.jc_ipv4_network_end'
        db.alter_column(u'jails_jailsconfiguration', 'jc_ipv4_network_end', self.gf('freenasUI.freeadmin.models.Network4Field')(max_length=18))

    models = {
        u'jails.jails': {
            'Meta': {'object_name': 'Jails'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jail_alias_bridge_ipv4': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_alias_bridge_ipv6': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_alias_ipv4': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_alias_ipv6': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_autostart': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'max_length': '120'}),
            'jail_bridge_ipv4': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_bridge_ipv6': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_defaultrouter_ipv4': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'null': 'True', 'blank': 'True'}),
            'jail_defaultrouter_ipv6': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'null': 'True', 'blank': 'True'}),
            'jail_host': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'jail_ipv4': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_ipv6': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_mac': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'jail_nat': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'jail_status': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'jail_type': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'jail_vnet': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'max_length': '120'})
        },
        u'jails.jailsconfiguration': {
            'Meta': {'object_name': 'JailsConfiguration'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jc_collectionurl': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'jc_ipv4_network': ('freenasUI.freeadmin.models.fields.Network4Field', [], {'max_length': '18', 'blank': 'True'}),
            'jc_ipv4_network_end': ('freenasUI.freeadmin.models.fields.Network4Field', [], {'max_length': '18', 'blank': 'True'}),
            'jc_ipv4_network_start': ('freenasUI.freeadmin.models.fields.Network4Field', [], {'max_length': '18', 'blank': 'True'}),
            'jc_ipv6_network': ('freenasUI.freeadmin.models.fields.Network6Field', [], {'max_length': '43', 'blank': 'True'}),
            'jc_ipv6_network_end': ('freenasUI.freeadmin.models.fields.Network6Field', [], {'max_length': '43', 'blank': 'True'}),
            'jc_ipv6_network_start': ('freenasUI.freeadmin.models.fields.Network6Field', [], {'max_length': '43', 'blank': 'True'}),
            'jc_path': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'jails.jailtemplate': {
            'Meta': {'object_name': 'JailTemplate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jt_name': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'jt_url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'jails.nullmountpoint': {
            'Meta': {'object_name': 'NullMountPoint'},
            'destination': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jail': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        }
    }

    complete_apps = ['jails']
