# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0007_remove_batchquestion_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='batchquestion',
            name='group',
            field=models.ForeignKey(related_name='questions', blank=True, to='survey.RespondentGroup', null=True),
        ),
    ]
