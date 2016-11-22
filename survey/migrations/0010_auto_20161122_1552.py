# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0009_auto_20161116_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionloop',
            name='loop_label',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='fixedloopcount',
            name='loop',
            field=models.OneToOneField(related_name='fixedloopcount', to='survey.QuestionLoop'),
        ),
        migrations.AlterField(
            model_name='previousanswercount',
            name='loop',
            field=models.OneToOneField(related_name='previousanswercount', to='survey.QuestionLoop'),
        ),
    ]
