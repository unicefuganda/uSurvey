# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0015_auto_20161203_1815'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionloop',
            name='loop_prompt',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
