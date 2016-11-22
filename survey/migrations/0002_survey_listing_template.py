# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='listing_template',
            field=models.ForeignKey(related_name='surveys', default=1, to='survey.ListingTemplate'),
            preserve_default=False,
        ),
    ]
