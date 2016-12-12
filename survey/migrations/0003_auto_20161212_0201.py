# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0002_auto_20161212_0140'),
    ]

    operations = [
        migrations.AlterField(
            model_name='respondentgroupcondition',
            name='test_question',
            field=models.ForeignKey(related_name='group_condition', to='survey.ParameterTemplate'),
        ),
    ]
