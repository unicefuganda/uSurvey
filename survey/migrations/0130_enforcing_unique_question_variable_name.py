# -*- coding: utf-8 -*-
import datetime
from random import randint
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        all_question_identifier = orm['survey.question'].objects.values_list('identifier', flat=True)
        duplicates = filter(lambda identifier: all_question_identifier.count(identifier) > 1, list(set(all_question_identifier)))
        for identifier in list(set(duplicates)) :
            for question in orm['survey_question'].objects.filter(identifier=identifier):
                question.identifier = identifier + "%d" % randint(0, 100)
                question.save()

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'locations.location': {
            'Meta': {'object_name': 'Location'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['locations.Location']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locations'", 'null': 'True', 'to': u"orm['locations.LocationType']"})
        },
        u'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True'})
        },
        u'locations.point': {
            'Meta': {'object_name': 'Point'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        'survey.aboutus': {
            'Meta': {'object_name': 'AboutUs'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        'survey.answerrule': {
            'Meta': {'object_name': 'AnswerRule'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batch_rule'", 'null': 'True', 'to': "orm['survey.Batch']"}),
            'condition': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'next_question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parent_question_rules'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rule'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'validate_with_max_value': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '2', 'null': 'True'}),
            'validate_with_min_value': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '2', 'null': 'True'}),
            'validate_with_option': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answer_rule'", 'null': 'True', 'to': "orm['survey.QuestionOption']"}),
            'validate_with_question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.Question']", 'null': 'True'}),
            'validate_with_value': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '2', 'null': 'True'})
        },
        'survey.backend': {
            'Meta': {'object_name': 'Backend'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'survey.batch': {
            'Meta': {'unique_together': "(('survey', 'name'),)", 'object_name': 'Batch'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '2', 'null': 'True'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batch'", 'null': 'True', 'to': "orm['survey.Survey']"})
        },
        'survey.batchlocationstatus': {
            'Meta': {'object_name': 'BatchLocationStatus'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'open_locations'", 'null': 'True', 'to': "orm['survey.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'open_batches'", 'null': 'True', 'to': u"orm['locations.Location']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'non_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'survey.batchquestionorder': {
            'Meta': {'object_name': 'BatchQuestionOrder'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batch_question_order'", 'to': "orm['survey.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_batch_order'", 'to': "orm['survey.Question']"})
        },
        'survey.enumerationarea': {
            'Meta': {'object_name': 'EnumerationArea'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'enumeration_area'", 'null': 'True', 'to': u"orm['locations.Location']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'enumeration_area'", 'null': 'True', 'to': "orm['survey.Survey']"})
        },
        'survey.formula': {
            'Meta': {'object_name': 'Formula'},
            'count': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'as_count'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'denominator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'as_denominator'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'denominator_options': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'denominator_options'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['survey.QuestionOption']"}),
            'groups': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'as_group'", 'null': 'True', 'to': "orm['survey.HouseholdMemberGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indicator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'formula'", 'null': 'True', 'to': "orm['survey.Indicator']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'numerator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'as_numerator'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'numerator_options': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'numerator_options'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['survey.QuestionOption']"})
        },
        'survey.groupcondition': {
            'Meta': {'unique_together': "(('value', 'attribute', 'condition'),)", 'object_name': 'GroupCondition'},
            'attribute': ('django.db.models.fields.CharField', [], {'default': "'AGE'", 'max_length': '20'}),
            'condition': ('django.db.models.fields.CharField', [], {'default': "'EQUALS'", 'max_length': '20'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'conditions'", 'symmetrical': 'False', 'to': "orm['survey.HouseholdMemberGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'survey.household': {
            'Meta': {'object_name': 'Household'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'ea': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'household_enumeration_area'", 'null': 'True', 'to': "orm['survey.EnumerationArea']"}),
            'household_code': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'investigator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'households'", 'null': 'True', 'to': "orm['survey.Investigator']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'random_sample_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'survey_household'", 'null': 'True', 'to': "orm['survey.Survey']"}),
            'uid': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'})
        },
        'survey.householdbatchcompletion': {
            'Meta': {'object_name': 'HouseholdBatchCompletion'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batch_completion_households'", 'null': 'True', 'to': "orm['survey.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batch_completion_batches'", 'null': 'True', 'to': "orm['survey.Household']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'investigator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batch_completion_completed_households'", 'null': 'True', 'to': "orm['survey.Investigator']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        'survey.householdhead': {
            'Meta': {'object_name': 'HouseholdHead', '_ormbases': ['survey.HouseholdMember']},
            u'householdmember_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['survey.HouseholdMember']", 'unique': 'True', 'primary_key': 'True'}),
            'level_of_education': ('django.db.models.fields.CharField', [], {'default': "'Primary'", 'max_length': '100', 'null': 'True'}),
            'occupation': ('django.db.models.fields.CharField', [], {'default': "'16'", 'max_length': '100'}),
            'resident_since_month': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5'}),
            'resident_since_year': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1984'})
        },
        'survey.householdmember': {
            'Meta': {'object_name': 'HouseholdMember'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'household_member'", 'to': "orm['survey.Household']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'male': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'survey.householdmemberbatchcompletion': {
            'Meta': {'object_name': 'HouseholdMemberBatchCompletion'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'completed_households'", 'null': 'True', 'to': "orm['survey.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'completed_batches'", 'null': 'True', 'to': "orm['survey.Household']"}),
            'householdmember': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'completed_member_batches'", 'null': 'True', 'to': "orm['survey.HouseholdMember']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'investigator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'completed_batches'", 'null': 'True', 'to': "orm['survey.Investigator']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        'survey.householdmembergroup': {
            'Meta': {'object_name': 'HouseholdMemberGroup'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'unique': 'True', 'max_length': '5'})
        },
        'survey.indicator': {
            'Meta': {'object_name': 'Indicator'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.Batch']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measure': ('django.db.models.fields.CharField', [], {'default': "'Percentage'", 'max_length': '255'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'indicator'", 'to': "orm['survey.QuestionModule']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'survey.investigator': {
            'Meta': {'object_name': 'Investigator'},
            'age': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.Backend']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'ea': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'enumeration_area'", 'null': 'True', 'to': "orm['survey.EnumerationArea']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'English'", 'max_length': '100', 'null': 'True'}),
            'level_of_education': ('django.db.models.fields.CharField', [], {'default': "'Primary'", 'max_length': '100', 'null': 'True'}),
            'male': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mobile_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'weights': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        'survey.locationautocomplete': {
            'Meta': {'object_name': 'LocationAutoComplete'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['locations.Location']", 'null': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'survey.locationcode': {
            'Meta': {'object_name': 'LocationCode'},
            'code': ('django.db.models.fields.CharField', [], {'default': '0', 'max_length': '10'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'code'", 'to': u"orm['locations.Location']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        'survey.locationtypedetails': {
            'Meta': {'object_name': 'LocationTypeDetails'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'details'", 'null': 'True', 'to': u"orm['locations.Location']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'has_code': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length_of_code': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'details'", 'to': u"orm['locations.LocationType']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'survey.locationweight': {
            'Meta': {'object_name': 'LocationWeight'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'weight'", 'to': u"orm['locations.Location']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'selection_probability': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'location_weight'", 'to': "orm['survey.Survey']"})
        },
        'survey.multichoiceanswer': {
            'Meta': {'object_name': 'MultiChoiceAnswer'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.QuestionOption']", 'null': 'True'}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.Batch']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'multichoiceanswer'", 'null': 'True', 'to': "orm['survey.Household']"}),
            'householdmember': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'multichoiceanswer'", 'null': 'True', 'to': "orm['survey.HouseholdMember']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'investigator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'multichoiceanswer'", 'null': 'True', 'to': "orm['survey.Investigator']"}),
            'is_old': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'multichoiceanswer'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'rule_applied': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.AnswerRule']", 'null': 'True'})
        },
        'survey.numericalanswer': {
            'Meta': {'object_name': 'NumericalAnswer'},
            'answer': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '5', 'null': 'True'}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.Batch']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'numericalanswer'", 'null': 'True', 'to': "orm['survey.Household']"}),
            'householdmember': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'numericalanswer'", 'null': 'True', 'to': "orm['survey.HouseholdMember']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'investigator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'numericalanswer'", 'null': 'True', 'to': "orm['survey.Investigator']"}),
            'is_old': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'numericalanswer'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'rule_applied': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.AnswerRule']", 'null': 'True'})
        },
        'survey.question': {
            'Meta': {'object_name': 'Question'},
            'answer_type': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'batches': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'questions'", 'null': 'True', 'to': "orm['survey.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_group'", 'null': 'True', 'to': "orm['survey.HouseholdMemberGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'module_question'", 'null': 'True', 'to': "orm['survey.QuestionModule']"}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '2', 'null': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'subquestion': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'survey.questionmodule': {
            'Meta': {'object_name': 'QuestionModule'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'survey.questionoption': {
            'Meta': {'ordering': "['order']", 'object_name': 'QuestionOption'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '2', 'null': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'survey.randomhouseholdselection': {
            'Meta': {'object_name': 'RandomHouseHoldSelection'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'no_of_households': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'selected_households': ('django.db.models.fields.TextField', [], {}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'random_household'", 'null': 'True', 'to': "orm['survey.Survey']"})
        },
        'survey.survey': {
            'Meta': {'object_name': 'Survey'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'has_sampling': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'sample_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10', 'max_length': '2'}),
            'type': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'survey.textanswer': {
            'Meta': {'object_name': 'TextAnswer'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.Batch']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'textanswer'", 'null': 'True', 'to': "orm['survey.Household']"}),
            'householdmember': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'textanswer'", 'null': 'True', 'to': "orm['survey.HouseholdMember']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'investigator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'textanswer'", 'null': 'True', 'to': "orm['survey.Investigator']"}),
            'is_old': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'textanswer'", 'null': 'True', 'to': "orm['survey.Question']"}),
            'rule_applied': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['survey.AnswerRule']", 'null': 'True'})
        },
        'survey.unknowndobattribute': {
            'Meta': {'object_name': 'UnknownDOBAttribute'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'household_member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'unknown_dob_attribute'", 'to': "orm['survey.HouseholdMember']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'survey.uploaderrorlog': {
            'Meta': {'object_name': 'UploadErrorLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'row_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'survey.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'userprofile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['survey']
    symmetrical = True
