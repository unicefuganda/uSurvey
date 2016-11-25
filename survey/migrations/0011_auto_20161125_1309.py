# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0010_auto_20161122_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fixedloopcount',
            name='value',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='location',
            name='code',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='questionloop',
            name='repeat_logic',
            field=models.CharField(max_length=64, choices=[(b'', b'User Defined'), (b'fixedloopcount', b'Fixed number of Repeats'), (b'previousanswercount', b'Response from previous question')]),
        ),
    ]
