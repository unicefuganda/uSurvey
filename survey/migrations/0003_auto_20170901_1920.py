# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0002_auto_20170814_0147'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='batch',
            options={'ordering': ('modified', 'created')},
        ),
        migrations.AlterModelOptions(
            name='interviewer',
            options={'ordering': ('modified', 'created')},
        ),
        migrations.AlterModelOptions(
            name='listingtemplate',
            options={'ordering': ('modified', 'created')},
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ('modified', 'created')},
        ),
        migrations.AlterModelOptions(
            name='questionset',
            options={'ordering': ('modified', 'created')},
        ),
    ]
