# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0008_batchquestion_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='FixedLoopCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PreviousAnswerCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionLoop',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('repeat_logic', models.CharField(max_length=64, choices=[(b'', b'User Defined'), (b'ModelBase', b'Fixed number of Repeats'), (b'ModelBase', b'Response from previous question')])),
                ('loop_ender', models.OneToOneField(related_name='loop_ended', to='survey.Question')),
                ('loop_starter', models.OneToOneField(related_name='loop_started', to='survey.Question')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='previousanswercount',
            name='loop',
            field=models.ForeignKey(related_name='previousanswercount', to='survey.QuestionLoop'),
        ),
        migrations.AddField(
            model_name='previousanswercount',
            name='value',
            field=models.ForeignKey(related_name='loop_count_identifier', to='survey.Question'),
        ),
        migrations.AddField(
            model_name='fixedloopcount',
            name='loop',
            field=models.ForeignKey(related_name='fixedloopcount', to='survey.QuestionLoop'),
        ),
    ]
