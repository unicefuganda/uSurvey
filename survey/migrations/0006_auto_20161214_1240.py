# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0005_auto_20161214_1136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interviewer',
            name='ea',
            field=models.ForeignKey(related_name='interviewers', verbose_name=b'Enumeration Area', blank=True, to='survey.EnumerationArea', null=True),
        ),
    ]
