# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0013_auto_20161129_2225'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='mandatory',
            field=models.BooleanField(default=True),
        ),
    ]
