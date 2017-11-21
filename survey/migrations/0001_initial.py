# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import survey.models.interviews
import django_extensions.db.fields
import mptt.fields
from django.conf import settings
import django.db.models.deletion
import survey.models.odk_submission
import survey.models.interviewer
import survey.models.about_us_content


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutUs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('question_type', models.CharField(max_length=100)),
                ('identifier', models.CharField(max_length=200, db_index=True)),
                ('as_text', models.CharField(max_length=200, db_index=True)),
                ('as_value', models.CharField(max_length=200, db_index=True)),
            ],
            options={
                'abstract': False,
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='AnswerAccessDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('answer_type', models.CharField(max_length=100, choices=[('Audio Answer', 'Audio Answer'), (b'Auto Generated', b'Auto Generated'), ('Date Answer', 'Date Answer'), ('Geopoint Answer', 'Geopoint Answer'), ('Image Answer', 'Image Answer'), ('Multi Choice Answer', 'Multi Choice Answer'), ('Multi Select Answer', 'Multi Select Answer'), ('Numerical Answer', 'Numerical Answer'), ('Text Answer', 'Text Answer'), ('Video Answer', 'Video Answer')])),
                ('channel', models.CharField(max_length=100, choices=[('Ussd Access', 'Ussd Access'), ('Odk Access', 'Odk Access'), ('Web Access', 'Web Access')])),
            ],
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('upload_field_name', models.CharField(max_length=100)),
                ('media_file', models.FileField(upload_to=survey.models.odk_submission.upload_to)),
                ('mimetype', models.CharField(default=b'', max_length=50, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Backend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='BatchChannel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('channel', models.CharField(max_length=100, choices=[('Ussd Access', 'Ussd Access'), ('Odk Access', 'Odk Access'), ('Web Access', 'Web Access')])),
            ],
        ),
        migrations.CreateModel(
            name='BatchCommencement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BatchLocationStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('non_response', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CriterionTestArgument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('position', models.PositiveIntegerField()),
                ('param', models.CharField(max_length=100)),
            ],
            options={
                'get_latest_by': 'position',
            },
        ),
        migrations.CreateModel(
            name='EnumerationArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=200, null=True, db_index=True)),
                ('code', models.CharField(max_length=200, unique=True, null=True, editable=False, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FixedLoopCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('value', models.PositiveIntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GroupTestArgument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('position', models.PositiveIntegerField()),
                ('param', models.CharField(max_length=100)),
            ],
            options={
                'get_latest_by': 'position',
            },
        ),
        migrations.CreateModel(
            name='Indicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(null=True)),
                ('display_on_dashboard', models.BooleanField(default=False)),
                ('formulae', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='IndicatorCriteriaTestArgument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('position', models.PositiveIntegerField()),
                ('param', models.CharField(max_length=100)),
            ],
            options={
                'get_latest_by': 'position',
            },
        ),
        migrations.CreateModel(
            name='IndicatorVariable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=150)),
                ('description', models.TextField()),
                ('indicator', models.ForeignKey(related_name='variables', blank=True, to='survey.Indicator', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='IndicatorVariableCriteria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('validation_test', models.CharField(max_length=200, verbose_name=b'Condition', choices=[(b'starts_with', b'starts_with'), (b'ends_with', b'ends_with'), (b'equals', b'equals'), (b'between', b'between'), (b'less_than', b'less_than'), (b'greater_than', b'greater_than'), (b'contains', b'contains')])),
            ],
        ),
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('closure_date', models.DateTimeField(verbose_name=b'Completion Date', null=True, editable=False, blank=True)),
                ('test_data', models.BooleanField(default=False)),
                ('ea', models.ForeignKey(related_name='interviews', to='survey.EnumerationArea', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Interviewer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=100)),
                ('gender', models.CharField(default=b'1', max_length=10, verbose_name=b'Gender', choices=[(b'1', b'M'), (b'0', b'F')])),
                ('date_of_birth', models.DateField(null=True, validators=[survey.models.interviewer.validate_min_date_of_birth, survey.models.interviewer.validate_max_date_of_birth])),
                ('level_of_education', models.CharField(default=b'Primary', max_length=100, null=True, verbose_name=b'Education', choices=[(b'Did not attend school', b'Did not attend school'), (b'Nursery', b'Nursery'), (b'Primary', b'Primary'), (b"'O' Level", b"'O' Level"), (b"'A' Level", b"'A' Level"), (b'Tertiary', b'Tertiary'), (b'University', b'University')])),
                ('is_blocked', models.BooleanField(default=False)),
                ('language', models.CharField(default=b'English', max_length=100, null=True, verbose_name=b'Preferred language', choices=[(b'English', b'English'), (b'Luganda', b'Luganda'), (b'Runyankore-Rukiga', b'Runyankore-Rukiga'), (b'Runyoro-Rutoro', b'Runyoro-Rutoro'), (b'Swahili', b'Swahili'), (b'Ateso-Karimojong', b'Ateso-Karimojong'), (b'Luo', b'Luo'), (b'Lugbara', b'Lugbara')])),
                ('weights', models.FloatField(default=0)),
                ('ea', models.ForeignKey(related_name='interviewers', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Enumeration Area', blank=True, to='survey.EnumerationArea', null=True)),
            ],
            options={
                'ordering': ('modified', 'created'),
            },
        ),
        migrations.CreateModel(
            name='InterviewerAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('user_identifier', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True, verbose_name=b'Activated')),
                ('reponse_timeout', models.PositiveIntegerField(default=1000, help_text=b'Max time to wait for response before ending interview', null=True, blank=True)),
                ('duration', models.CharField(default=b'H', max_length=100, null=True, blank=True, choices=[(b'D', b'Days'), (b'H', b'Hours'), (b'M', b'Minutes'), (b'S', b'Seconds')])),
            ],
        ),
        migrations.CreateModel(
            name='ListingSample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('interview', models.ForeignKey(related_name='listing_samples', to='survey.Interview')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('code', models.CharField(max_length=200, null=True, blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='LocationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(unique=True, max_length=200)),
                ('location_code', models.PositiveIntegerField(null=True, blank=True)),
                ('slug', models.SlugField()),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='sub_types', blank=True, to='survey.LocationType', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LocationWeight',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('selection_probability', models.FloatField(default=1.0)),
                ('location', models.ForeignKey(related_name='weight', to='survey.Location')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NonResponseAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('value', models.CharField(max_length=200)),
                ('interview', models.ForeignKey(related_name='non_response_answers', to='survey.Interview')),
                ('interviewer', models.ForeignKey(related_name='non_response_answers', to='survey.Interviewer', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ODKFileDownload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ODKSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('form_id', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256, null=True, blank=True)),
                ('instance_id', models.CharField(max_length=256)),
                ('instance_name', models.CharField(max_length=256, null=True, blank=True)),
                ('xml', models.TextField()),
                ('status', models.IntegerField(default=1, choices=[(1, b'Started'), (2, b'Completed')])),
                ('ea', models.ForeignKey(related_name='odk_submissions', blank=True, to='survey.EnumerationArea', null=True)),
                ('interviewer', models.ForeignKey(related_name='odk_submissions', to='survey.Interviewer')),
                ('interviews', models.ManyToManyField(related_name='odk_submissions', to='survey.Interview')),
            ],
        ),
        migrations.CreateModel(
            name='Point',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('latitude', models.DecimalField(max_digits=13, decimal_places=10)),
                ('longitude', models.DecimalField(max_digits=13, decimal_places=10)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PreviousAnswerCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('identifier', models.CharField(max_length=100, verbose_name=b'Variable Name')),
                ('text', models.CharField(max_length=250)),
                ('answer_type', models.CharField(max_length=100, choices=[('Audio Answer', 'Audio Answer'), (b'Auto Generated', b'Auto Generated'), ('Date Answer', 'Date Answer'), ('Geopoint Answer', 'Geopoint Answer'), ('Image Answer', 'Image Answer'), ('Multi Choice Answer', 'Multi Choice Answer'), ('Multi Select Answer', 'Multi Select Answer'), ('Numerical Answer', 'Numerical Answer'), ('Text Answer', 'Text Answer'), ('Video Answer', 'Video Answer')])),
                ('mandatory', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('modified', 'created'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionFlow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('question_type', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('desc', models.CharField(max_length=200, null=True, blank=True)),
                ('next_question_type', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='QuestionLoop',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('repeat_logic', models.CharField(blank=True, max_length=64, null=True, choices=[(b'', b'User Defined'), (b'fixedloopcount', b'Fixed number of Repeats'), (b'previousanswercount', b'Response from previous question')])),
                ('loop_prompt', models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('text', models.CharField(max_length=150)),
                ('order', models.PositiveIntegerField()),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='QuestionSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(default=b'', max_length=100, db_index=True)),
                ('description', models.CharField(max_length=300, null=True, blank=True)),
            ],
            options={
                'ordering': ('modified', 'created'),
            },
        ),
        migrations.CreateModel(
            name='QuestionSetChannel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('channel', models.CharField(max_length=100, choices=[('Ussd Access', 'Ussd Access'), ('Odk Access', 'Odk Access'), ('Web Access', 'Web Access')])),
            ],
        ),
        migrations.CreateModel(
            name='RandomizationCriterion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('validation_test', models.CharField(blank=True, max_length=200, null=True, choices=[(b'starts_with', b'starts_with'), (b'ends_with', b'ends_with'), (b'equals', b'equals'), (b'between', b'between'), (b'less_than', b'less_than'), (b'greater_than', b'greater_than'), (b'contains', b'contains')])),
            ],
        ),
        migrations.CreateModel(
            name='RespondentGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RespondentGroupCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('validation_test', models.CharField(blank=True, max_length=200, null=True, choices=[(b'starts_with', b'starts_with'), (b'ends_with', b'ends_with'), (b'equals', b'equals'), (b'between', b'between'), (b'less_than', b'less_than'), (b'greater_than', b'greater_than'), (b'contains', b'contains')])),
                ('respondent_group', models.ForeignKey(related_name='group_conditions', to='survey.RespondentGroup')),
            ],
        ),
        migrations.CreateModel(
            name='ResponseValidation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('validation_test', models.CharField(max_length=200, choices=[(b'starts_with', b'starts_with'), (b'ends_with', b'ends_with'), (b'equals', b'equals'), (b'between', b'between'), (b'less_than', b'less_than'), (b'greater_than', b'greater_than'), (b'contains', b'contains')])),
                ('constraint_message', models.TextField(default=b'', null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SuccessStories',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=100)),
                ('content', models.TextField()),
                ('image', models.FileField(upload_to=survey.models.about_us_content.content_file_name)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(default=b'', unique=True, max_length=100)),
                ('description', models.CharField(max_length=300, null=True)),
                ('has_sampling', models.BooleanField(default=True, verbose_name=b'Survey Type')),
                ('sample_size', models.PositiveIntegerField(default=10)),
                ('random_sample_label', models.TextField(help_text=b'Include double curly brackets to automatically insert identifiers from the listing form e.g {{structure_address}}', null=True, verbose_name=b'Randomly selected data label', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'permissions': (('view_completed_survey', 'Can view Completed interviewers'),),
            },
        ),
        migrations.CreateModel(
            name='SurveyAllocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('stage', models.CharField(blank=True, max_length=20, null=True, choices=[(1, b'LISTING'), (2, b'SURVEY')])),
                ('status', models.IntegerField(default=0, choices=[(0, b'PENDING'), (2, b'DEALLOCATED'), (1, b'COMPLETED')])),
                ('allocation_ea', models.ForeignKey(related_name='survey_allocations', to='survey.EnumerationArea')),
                ('interviewer', models.ForeignKey(related_name='assignments', to='survey.Interviewer')),
                ('survey', models.ForeignKey(related_name='work_allocation', to='survey.Survey')),
            ],
        ),
        migrations.CreateModel(
            name='TemplateOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('text', models.CharField(max_length=150)),
                ('order', models.PositiveIntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TemplateQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('identifier', models.CharField(max_length=100, verbose_name=b'Variable Name')),
                ('text', models.CharField(max_length=250)),
                ('answer_type', models.CharField(max_length=100, choices=[('Audio Answer', 'Audio Answer'), (b'Auto Generated', b'Auto Generated'), ('Date Answer', 'Date Answer'), ('Geopoint Answer', 'Geopoint Answer'), ('Image Answer', 'Image Answer'), ('Multi Choice Answer', 'Multi Choice Answer'), ('Multi Select Answer', 'Multi Select Answer'), ('Numerical Answer', 'Numerical Answer'), ('Text Answer', 'Text Answer'), ('Video Answer', 'Video Answer')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TestArgument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('position', models.PositiveIntegerField()),
            ],
            options={
                'get_latest_by': 'position',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('mobile_number', models.CharField(unique=True, max_length=12, validators=[django.core.validators.MinLengthValidator(7), django.core.validators.MaxLengthValidator(12)])),
                ('user', models.OneToOneField(related_name='userprofile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AudioAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
                ('value', models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/files/answerFiles')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer', survey.models.interviews.FileAnswerMixin),
        ),
        migrations.CreateModel(
            name='AutoResponse',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
                ('value', models.CharField(max_length=100, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer',),
        ),
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('questionset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.QuestionSet')),
                ('order', models.PositiveIntegerField(null=True)),
            ],
            options={
                'ordering': ('modified', 'created'),
            },
            bases=('survey.questionset',),
        ),
        migrations.CreateModel(
            name='BatchQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Question')),
                ('group', models.ForeignKey(related_name='questions', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='survey.RespondentGroup', null=True)),
                ('module', models.ForeignKey(related_name='questions', on_delete=django.db.models.deletion.SET_NULL, default=b'', blank=True, to='survey.QuestionModule', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.question',),
        ),
        migrations.CreateModel(
            name='DateAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
                ('value', models.DateField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer',),
        ),
        migrations.CreateModel(
            name='DateArgument',
            fields=[
                ('testargument_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.TestArgument')),
                ('param', models.DateField()),
            ],
            bases=('survey.testargument',),
        ),
        migrations.CreateModel(
            name='GeopointAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer',),
        ),
        migrations.CreateModel(
            name='ImageAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
                ('value', models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/files/answerFiles')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer', survey.models.interviews.FileAnswerMixin),
        ),
        migrations.CreateModel(
            name='ListingTemplate',
            fields=[
                ('questionset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.QuestionSet')),
            ],
            options={
                'ordering': ('modified', 'created'),
            },
            bases=('survey.questionset',),
        ),
        migrations.CreateModel(
            name='MultiChoiceAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer',),
        ),
        migrations.CreateModel(
            name='MultiSelectAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer',),
        ),
        migrations.CreateModel(
            name='NumberArgument',
            fields=[
                ('testargument_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.TestArgument')),
                ('param', models.IntegerField()),
            ],
            bases=('survey.testargument',),
        ),
        migrations.CreateModel(
            name='NumericalAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
                ('value', models.PositiveIntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer',),
        ),
        migrations.CreateModel(
            name='ODKAccess',
            fields=[
                ('intervieweraccess_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.InterviewerAccess')),
                ('odk_token', models.CharField(default=b'12345', max_length=10)),
            ],
            bases=('survey.intervieweraccess',),
        ),
        migrations.CreateModel(
            name='ODKGeoPoint',
            fields=[
                ('point_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Point')),
                ('altitude', models.DecimalField(max_digits=10, decimal_places=3)),
                ('precision', models.DecimalField(max_digits=10, decimal_places=3)),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.point',),
        ),
        migrations.CreateModel(
            name='ParameterQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Question')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.question',),
        ),
        migrations.CreateModel(
            name='ParameterTemplate',
            fields=[
                ('templatequestion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.TemplateQuestion')),
            ],
            bases=('survey.templatequestion',),
        ),
        migrations.CreateModel(
            name='QuestionTemplate',
            fields=[
                ('templatequestion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.TemplateQuestion')),
                ('module', models.ForeignKey(related_name='question_templates', blank=True, to='survey.QuestionModule', null=True)),
            ],
            bases=('survey.templatequestion',),
        ),
        migrations.CreateModel(
            name='SurveyParameterList',
            fields=[
                ('questionset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.QuestionSet')),
                ('batch', models.OneToOneField(related_name='parameter_list', null=True, blank=True, to='survey.Batch')),
            ],
            bases=('survey.questionset',),
        ),
        migrations.CreateModel(
            name='TextAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
                ('value', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer',),
        ),
        migrations.CreateModel(
            name='TextArgument',
            fields=[
                ('testargument_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.TestArgument')),
                ('param', models.TextField()),
            ],
            bases=('survey.testargument',),
        ),
        migrations.CreateModel(
            name='USSDAccess',
            fields=[
                ('intervieweraccess_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.InterviewerAccess')),
                ('aggregator', models.CharField(default=b'testAggregator', max_length=100, null=True, blank=True, choices=[(b'testAggregator', b'testAggregator')])),
            ],
            bases=('survey.intervieweraccess',),
        ),
        migrations.CreateModel(
            name='VideoAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.Answer')),
                ('value', models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/files/answerFiles')),
            ],
            options={
                'abstract': False,
            },
            bases=('survey.answer', survey.models.interviews.FileAnswerMixin),
        ),
        migrations.CreateModel(
            name='WebAccess',
            fields=[
                ('intervieweraccess_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.InterviewerAccess')),
            ],
            bases=('survey.intervieweraccess',),
        ),
        migrations.AddField(
            model_name='testargument',
            name='validation',
            field=models.ForeignKey(related_name='testarguments', to='survey.ResponseValidation', null=True),
        ),
        migrations.AddField(
            model_name='templatequestion',
            name='response_validation',
            field=models.ForeignKey(related_name='templatequestion', verbose_name=b'Validation Rule', blank=True, to='survey.ResponseValidation', null=True),
        ),
        migrations.AddField(
            model_name='templateoption',
            name='question',
            field=models.ForeignKey(related_name='options', to='survey.TemplateQuestion', null=True),
        ),
        migrations.AddField(
            model_name='survey',
            name='email_group',
            field=models.ManyToManyField(related_name='email_surveys', to='survey.UserProfile'),
        ),
        migrations.AddField(
            model_name='survey',
            name='preferred_listing',
            field=models.ForeignKey(related_name='listing_users', blank=True, to='survey.Survey', help_text=b'Select which survey listing to reuse. Leave empty for fresh listing', null=True),
        ),
        migrations.AddField(
            model_name='randomizationcriterion',
            name='listing_question',
            field=models.ForeignKey(related_name='criteria', to='survey.Question'),
        ),
        migrations.AddField(
            model_name='randomizationcriterion',
            name='survey',
            field=models.ForeignKey(related_name='randomization_criteria', to='survey.Survey'),
        ),
        migrations.AddField(
            model_name='questionsetchannel',
            name='qset',
            field=models.ForeignKey(related_name='access_channels', to='survey.QuestionSet'),
        ),
        migrations.AddField(
            model_name='questionset',
            name='start_question',
            field=models.OneToOneField(related_name='qset_started', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='survey.Question'),
        ),
        migrations.AddField(
            model_name='questionoption',
            name='question',
            field=models.ForeignKey(related_name='options', to='survey.Question', null=True),
        ),
        migrations.AddField(
            model_name='questionloop',
            name='loop_ender',
            field=models.OneToOneField(related_name='loop_ended', to='survey.Question'),
        ),
        migrations.AddField(
            model_name='questionloop',
            name='loop_starter',
            field=models.OneToOneField(related_name='loop_started', to='survey.Question'),
        ),
        migrations.AddField(
            model_name='questionflow',
            name='next_question',
            field=models.ForeignKey(related_name='connecting_flows', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='survey.Question', null=True),
        ),
        migrations.AddField(
            model_name='questionflow',
            name='question',
            field=models.ForeignKey(related_name='flows', to='survey.Question'),
        ),
        migrations.AddField(
            model_name='questionflow',
            name='validation',
            field=models.ForeignKey(blank=True, to='survey.ResponseValidation', null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='qset',
            field=models.ForeignKey(related_name='questions', to='survey.QuestionSet'),
        ),
        migrations.AddField(
            model_name='question',
            name='response_validation',
            field=models.ForeignKey(related_name='question', verbose_name=b'Validation Rule', blank=True, to='survey.ResponseValidation', null=True),
        ),
        migrations.AddField(
            model_name='previousanswercount',
            name='loop',
            field=models.OneToOneField(related_name='previousanswercount', to='survey.QuestionLoop'),
        ),
        migrations.AddField(
            model_name='previousanswercount',
            name='value',
            field=models.ForeignKey(related_name='loop_count_identifier', to='survey.Question'),
        ),
        migrations.AddField(
            model_name='odksubmission',
            name='question_set',
            field=models.ForeignKey(related_name='odk_submissions', blank=True, to='survey.QuestionSet', null=True),
        ),
        migrations.AddField(
            model_name='odksubmission',
            name='survey',
            field=models.ForeignKey(related_name='odk_submissions', to='survey.Survey'),
        ),
        migrations.AddField(
            model_name='odkfiledownload',
            name='assignments',
            field=models.ManyToManyField(related_name='file_downloads', to='survey.SurveyAllocation'),
        ),
        migrations.AddField(
            model_name='locationweight',
            name='survey',
            field=models.ForeignKey(related_name='location_weight', to='survey.Survey'),
        ),
        migrations.AddField(
            model_name='location',
            name='coordinates',
            field=models.ManyToManyField(related_name='admin_div_locations', to='survey.Point'),
        ),
        migrations.AddField(
            model_name='location',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='sub_locations', blank=True, to='survey.Location', null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='type',
            field=models.ForeignKey(related_name='locations', to='survey.LocationType'),
        ),
        migrations.AddField(
            model_name='listingsample',
            name='survey',
            field=models.ForeignKey(related_name='listing_samples', to='survey.Survey'),
        ),
        migrations.AddField(
            model_name='intervieweraccess',
            name='interviewer',
            field=models.ForeignKey(related_name='intervieweraccess', to='survey.Interviewer'),
        ),
        migrations.AddField(
            model_name='interview',
            name='interview_channel',
            field=models.ForeignKey(related_name='interviews', to='survey.InterviewerAccess', null=True),
        ),
        migrations.AddField(
            model_name='interview',
            name='interview_reference',
            field=models.ForeignKey(related_name='follow_up_interviews', blank=True, to='survey.Interview', null=True),
        ),
        migrations.AddField(
            model_name='interview',
            name='interviewer',
            field=models.ForeignKey(related_name='interviews', to='survey.Interviewer', null=True),
        ),
        migrations.AddField(
            model_name='interview',
            name='last_question',
            field=models.ForeignKey(related_name='ongoing', blank=True, to='survey.Question', null=True),
        ),
        migrations.AddField(
            model_name='interview',
            name='question_set',
            field=models.ForeignKey(related_name='interviews', to='survey.QuestionSet'),
        ),
        migrations.AddField(
            model_name='interview',
            name='survey',
            field=models.ForeignKey(related_name='interviews', to='survey.Survey', null=True),
        ),
        migrations.AddField(
            model_name='interview',
            name='uploaded_by',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='indicatorvariablecriteria',
            name='test_question',
            field=models.ForeignKey(related_name='indicator_criteria', verbose_name=b'Filter', to='survey.Question'),
        ),
        migrations.AddField(
            model_name='indicatorvariablecriteria',
            name='variable',
            field=models.ForeignKey(related_name='criteria', to='survey.IndicatorVariable'),
        ),
        migrations.AddField(
            model_name='indicatorcriteriatestargument',
            name='criteria',
            field=models.ForeignKey(related_name='arguments', to='survey.IndicatorVariableCriteria'),
        ),
        migrations.AddField(
            model_name='indicator',
            name='question_set',
            field=models.ForeignKey(related_name='indicators', to='survey.QuestionSet'),
        ),
        migrations.AddField(
            model_name='indicator',
            name='survey',
            field=models.ForeignKey(related_name='indicators', to='survey.Survey'),
        ),
        migrations.AddField(
            model_name='grouptestargument',
            name='group_condition',
            field=models.ForeignKey(related_name='arguments', to='survey.RespondentGroupCondition'),
        ),
        migrations.AddField(
            model_name='fixedloopcount',
            name='loop',
            field=models.OneToOneField(related_name='fixedloopcount', to='survey.QuestionLoop'),
        ),
        migrations.AddField(
            model_name='enumerationarea',
            name='locations',
            field=models.ManyToManyField(related_name='enumeration_areas', to='survey.Location', db_index=True),
        ),
        migrations.AddField(
            model_name='criteriontestargument',
            name='test_condition',
            field=models.ForeignKey(related_name='arguments', to='survey.RandomizationCriterion'),
        ),
        migrations.AddField(
            model_name='batchlocationstatus',
            name='location',
            field=models.ForeignKey(related_name='open_batches', to='survey.Location', null=True),
        ),
        migrations.AddField(
            model_name='batchcommencement',
            name='ea',
            field=models.ForeignKey(related_name='commencement_registry', to='survey.EnumerationArea', null=True),
        ),
        migrations.AddField(
            model_name='batchcommencement',
            name='survey',
            field=models.ForeignKey(related_name='commencement_registry', to='survey.Survey', null=True),
        ),
        migrations.AddField(
            model_name='attachment',
            name='submission',
            field=models.ForeignKey(related_name='attachments', to='survey.ODKSubmission'),
        ),
        migrations.AlterUniqueTogether(
            name='answeraccessdefinition',
            unique_together=set([('answer_type', 'channel')]),
        ),
        migrations.AddField(
            model_name='answer',
            name='interview',
            field=models.ForeignKey(related_name='answer', to='survey.Interview'),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(related_name='answer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True),
        ),
        migrations.AddField(
            model_name='survey',
            name='listing_form',
            field=models.ForeignKey(related_name='survey_settings', blank=True, to='survey.ListingTemplate', null=True),
        ),
        migrations.AddField(
            model_name='respondentgroupcondition',
            name='test_question',
            field=models.ForeignKey(related_name='group_condition', to='survey.ParameterTemplate'),
        ),
        migrations.AlterUniqueTogether(
            name='questionsetchannel',
            unique_together=set([('qset', 'channel')]),
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('identifier', 'qset')]),
        ),
        migrations.AddField(
            model_name='multiselectanswer',
            name='value',
            field=models.ManyToManyField(to='survey.QuestionOption'),
        ),
        migrations.AddField(
            model_name='multichoiceanswer',
            name='value',
            field=models.ForeignKey(to='survey.QuestionOption', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='indicatorvariable',
            unique_together=set([('name', 'indicator')]),
        ),
        migrations.AddField(
            model_name='geopointanswer',
            name='value',
            field=models.ForeignKey(to='survey.ODKGeoPoint', null=True),
        ),
        migrations.AddField(
            model_name='batchlocationstatus',
            name='batch',
            field=models.ForeignKey(related_name='open_locations', to='survey.Batch', null=True),
        ),
        migrations.AddField(
            model_name='batchchannel',
            name='batch',
            field=models.ForeignKey(related_name='baccess_channels', to='survey.Batch'),
        ),
        migrations.AddField(
            model_name='batch',
            name='survey',
            field=models.ForeignKey(related_name='batches', to='survey.Survey', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='batchchannel',
            unique_together=set([('batch', 'channel')]),
        ),
    ]
