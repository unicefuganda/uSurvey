# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0004_auto_20161103_1805'),
    ]

    operations = [
        migrations.CreateModel(
            name='CriterionTestArgument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('position', models.PositiveIntegerField()),
                ('param', models.CharField(max_length=100)),
            ],
            options={
                'get_latest_by': 'position',
            },
        ),
        migrations.CreateModel(
            name='GroupTestArgument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('position', models.PositiveIntegerField()),
                ('param', models.CharField(max_length=100)),
            ],
            options={
                'get_latest_by': 'position',
            },
        ),
        migrations.CreateModel(
            name='MetricsForm',
            fields=[
                ('questionset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.QuestionSet')),
            ],
            bases=('survey.questionset',),
        ),
        migrations.CreateModel(
            name='RandomizationCriterion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('validation_test', models.CharField(blank=True, max_length=200, null=True, choices=[(b'starts_with', b'starts_with'), (b'ends_with', b'ends_with'), (b'equals', b'equals'), (b'between', b'between'), (b'less_than', b'less_than'), (b'greater_than', b'greater_than'), (b'contains', b'contains')])),
                ('listing_question', models.ForeignKey(related_name='criteria', to='survey.ListingQuestion')),
                ('listing_template', models.ForeignKey(related_name='criteria', to='survey.ListingTemplate')),
            ],
        ),
        migrations.CreateModel(
            name='RespondentGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
                ('metric_form', models.ForeignKey(related_name='respondent_group', to='survey.MetricsForm')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RespondentGroupCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('validation_test', models.CharField(blank=True, max_length=200, null=True, choices=[(b'starts_with', b'starts_with'), (b'ends_with', b'ends_with'), (b'equals', b'equals'), (b'between', b'between'), (b'less_than', b'less_than'), (b'greater_than', b'greater_than'), (b'contains', b'contains')])),
            ],
        ),
        migrations.CreateModel(
            name='SurveyMetric',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Question')),
                ('metric_form', models.ForeignKey(related_name='metric_form_questions', to='survey.MetricsForm')),
            ],
            bases=('survey.question',),
        ),
        migrations.AlterField(
            model_name='batchquestion',
            name='group',
            field=models.ForeignKey(related_name='questions', to='survey.RespondentGroup'),
        ),
        migrations.AddField(
            model_name='respondentgroupcondition',
            name='personal_info',
            field=models.ForeignKey(related_name='conditions', to='survey.SurveyMetric'),
        ),
        migrations.AddField(
            model_name='respondentgroupcondition',
            name='respondent_group',
            field=models.ForeignKey(related_name='conditions', to='survey.RespondentGroup'),
        ),
        migrations.AddField(
            model_name='grouptestargument',
            name='group_condition',
            field=models.ForeignKey(to='survey.RespondentGroupCondition'),
        ),
        migrations.AddField(
            model_name='criteriontestargument',
            name='group_condition',
            field=models.ForeignKey(to='survey.RandomizationCriterion'),
        ),
    ]
