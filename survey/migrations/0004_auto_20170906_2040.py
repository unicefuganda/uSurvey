# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_auto_20170901_1920'),
    ]

    operations = [
        migrations.AlterField(
            model_name='survey',
            name='name',
            field=models.CharField(default='test', unique=True, max_length=100),
            preserve_default=False,
        ),
    ]
