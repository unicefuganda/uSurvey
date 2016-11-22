# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_auto_20161102_1706'),
    ]

    operations = [
        migrations.RenameField(
            model_name='survey',
            old_name='listing_template',
            new_name='listing_form',
        ),
    ]
