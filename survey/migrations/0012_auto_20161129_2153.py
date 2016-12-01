# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0011_auto_20161125_1309'),
    ]

    operations = [
        migrations.CreateModel(
            name='ListingSample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('interview', models.ForeignKey(related_name='listing_samples', to='survey.Interview')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='audioanswer',
            name='loop_id',
        ),
        migrations.RemoveField(
            model_name='criteriontestargument',
            name='group_condition',
        ),
        migrations.RemoveField(
            model_name='dateanswer',
            name='loop_id',
        ),
        migrations.RemoveField(
            model_name='geopointanswer',
            name='loop_id',
        ),
        migrations.RemoveField(
            model_name='imageanswer',
            name='loop_id',
        ),
        migrations.RemoveField(
            model_name='multichoiceanswer',
            name='loop_id',
        ),
        migrations.RemoveField(
            model_name='multiselectanswer',
            name='loop_id',
        ),
        migrations.RemoveField(
            model_name='numericalanswer',
            name='loop_id',
        ),
        migrations.RemoveField(
            model_name='randomizationcriterion',
            name='listing_template',
        ),
        migrations.RemoveField(
            model_name='textanswer',
            name='loop_id',
        ),
        migrations.RemoveField(
            model_name='videoanswer',
            name='loop_id',
        ),
        migrations.AddField(
            model_name='criteriontestargument',
            name='test_condition',
            field=models.ForeignKey(related_name='arguments', default=1, to='survey.RandomizationCriterion'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='randomizationcriterion',
            name='survey',
            field=models.ForeignKey(related_name='randomization_criteria', default=1, to='survey.Survey'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='survey',
            name='listing_form',
            field=models.ForeignKey(related_name='survey_settings', to='survey.ListingTemplate', null=True),
        ),
        migrations.AlterField(
            model_name='survey',
            name='preferred_listing',
            field=models.ForeignKey(related_name='listing_users', blank=True, to='survey.Survey', help_text=b'Select which survey listing to reuse. Leave empty for fresh listing', null=True),
        ),
        migrations.AddField(
            model_name='listingsample',
            name='survey',
            field=models.ForeignKey(related_name='listing_samples', to='survey.Survey'),
        ),
    ]
