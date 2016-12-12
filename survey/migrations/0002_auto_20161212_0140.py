# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='respondentgroupcondition',
            name='test_question',
            field=models.OneToOneField(related_name='group_condition', default=1, to='survey.ParameterTemplate'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='grouptestargument',
            name='group_condition',
            field=models.ForeignKey(related_name='arguments', to='survey.RespondentGroupCondition'),
        ),
        migrations.AlterField(
            model_name='respondentgroupcondition',
            name='respondent_group',
            field=models.ForeignKey(related_name='group_conditions', to='survey.RespondentGroup'),
        ),
    ]
