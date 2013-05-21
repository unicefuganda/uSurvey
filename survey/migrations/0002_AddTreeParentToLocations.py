# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from rapidsms.contrib.locations.models import Location


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.add_column(u'locations_location', u'tree_parent', models.ForeignKey(Location, blank=True, null=True))
        db.add_column(u'locations_location', u'name', models.CharField(max_length=100, blank=False, null=False))
        db.add_column(u'locations_location', u'lft', models.PositiveIntegerField(db_index=True))
        db.add_column(u'locations_location', u'rght', models.PositiveIntegerField(db_index=True))
        db.add_column(u'locations_location', u'tree_id', models.PositiveIntegerField(db_index=True))
        db.add_column(u'locations_location', u'level', models.PositiveIntegerField(db_index=True))

    def backwards(self, orm):
        db.delete_column(u'locations_location', u'level')
        db.delete_column(u'locations_location', u'tree_id')
        db.delete_column(u'locations_location', u'rght')
        db.delete_column(u'locations_location', u'lft')
        db.delete_column(u'locations_location', u'name')
        db.delete_column(u'locations_location', u'tree_parent_id')

    models = {
        u'survey.investigator': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Investigator'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['survey']