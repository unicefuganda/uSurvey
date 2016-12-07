# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0014_question_mandatory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionloop',
            name='repeat_logic',
            field=models.CharField(blank=True, max_length=64, null=True, choices=[(b'', b'User Defined'), (b'fixedloopcount', b'Fixed number of Repeats'), (b'previousanswercount', b'Response from previous question')]),
        ),
    ]
