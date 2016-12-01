# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0012_auto_20161129_2153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='randomizationcriterion',
            name='listing_question',
            field=models.ForeignKey(related_name='criteria', to='survey.Question'),
        ),
    ]
