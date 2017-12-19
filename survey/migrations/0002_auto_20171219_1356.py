# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionflow',
            name='validation',
            field=models.ForeignKey(related_name='flows', blank=True, to='survey.ResponseValidation', null=True),
        ),
        migrations.AlterField(
            model_name='randomizationcriterion',
            name='validation_test',
            field=models.CharField(default='equals', max_length=200, choices=[(b'starts_with', b'starts_with'), (b'ends_with', b'ends_with'), (b'equals', b'equals'), (b'between', b'between'), (b'less_than', b'less_than'), (b'greater_than', b'greater_than'), (b'contains', b'contains')]),
            preserve_default=False,
        ),
    ]
