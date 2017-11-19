# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0004_auto_20170906_2040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionset',
            name='name',
            field=models.CharField(default=b'', max_length=100, db_index=True),
        ),
        migrations.AlterField(
            model_name='survey',
            name='name',
            field=models.CharField(default=b'', unique=True, max_length=100),
        ),
    ]
