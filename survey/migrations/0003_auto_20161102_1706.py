# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0002_survey_listing_template'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionSetChannel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('channel', models.CharField(max_length=100, choices=[('Ussd Access', 'Ussd Access'), ('Odk Access', 'Odk Access'), ('Web Access', 'Web Access')])),
                ('qset', models.ForeignKey(related_name='access_channels', to='survey.QuestionSet')),
            ],
        ),
        migrations.RemoveField(
            model_name='interview',
            name='survey',
        ),
        migrations.AddField(
            model_name='interview',
            name='question_set',
            field=models.ForeignKey(related_name='interviews', default=1, to='survey.QuestionSet'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='batchchannel',
            name='batch',
            field=models.ForeignKey(related_name='baccess_channels', to='survey.Batch'),
        ),
        migrations.AlterUniqueTogether(
            name='questionsetchannel',
            unique_together=set([('qset', 'channel')]),
        ),
    ]
