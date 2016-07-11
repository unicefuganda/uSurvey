# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='audioanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='dateanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='geopointanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='imageanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='multichoiceanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='multiselectanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='numericalanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='textanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='videoanswer',
            name='loop_id',
            field=models.IntegerField(default=-1),
        ),
    ]
