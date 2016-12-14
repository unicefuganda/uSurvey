# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0004_auto_20161213_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audioanswer',
            name='value',
            field=models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/answerFiles'),
        ),
        migrations.AlterField(
            model_name='imageanswer',
            name='value',
            field=models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/answerFiles'),
        ),
        migrations.AlterField(
            model_name='videoanswer',
            name='value',
            field=models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/answerFiles'),
        ),
    ]
