# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0006_auto_20161104_0524'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='batchquestion',
            name='group',
        ),
    ]
