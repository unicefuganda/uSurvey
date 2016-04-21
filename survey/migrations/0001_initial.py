# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import survey.models.interviewer
import django_extensions.db.fields
import mptt.fields
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone
import survey.models.odk_submission
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutUs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AnswerAccessDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('answer_type', models.CharField(max_length=100, choices=[('Numerical Answer', 'Numerical Answer'), ('Text Answer', 'Text Answer'), ('Multi Choice Answer', 'Multi Choice Answer'), ('Multi Select Answer', 'Multi Select Answer'), ('Date Answer', 'Date Answer'), ('Audio Answer', 'Audio Answer'), ('Video Answer', 'Video Answer'), ('Image Answer', 'Image Answer'), ('Geopoint Answer', 'Geopoint Answer')])),
                ('channel', models.CharField(max_length=100, choices=[('Ussd Access', 'Ussd Access'), ('Odk Access', 'Odk Access'), ('Web Access', 'Web Access')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('media_file', models.FileField(upload_to=survey.models.odk_submission.upload_to)),
                ('mimetype', models.CharField(default=b'', max_length=50, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AudioAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/mics/answerFiles')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Backend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('order', models.PositiveIntegerField(max_length=2, null=True)),
                ('name', models.CharField(max_length=100, null=True, db_index=True)),
                ('description', models.CharField(max_length=300, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BatchChannel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('channel', models.CharField(max_length=100, choices=[('Ussd Access', 'Ussd Access'), ('Odk Access', 'Odk Access'), ('Web Access', 'Web Access')])),
                ('batch', models.ForeignKey(related_name='access_channels', to='survey.Batch')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BatchCommencement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BatchLocationStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('non_response', models.BooleanField(default=False)),
                ('batch', models.ForeignKey(related_name='open_locations', to='survey.Batch', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DateAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.DateField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EnumerationArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=100, null=True)),
                ('code', models.CharField(max_length=200, unique=True, null=True, editable=False, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Formula',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GeopointAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.CharField(max_length=50)),
                ('attribute', models.CharField(default=b'AGE', max_length=20, choices=[(b'GENDER', b'GENDER'), (b'AGE', b'AGE'), (b'GENERAL', b'ROLE')])),
                ('condition', models.CharField(default=b'EQUALS', max_length=20, choices=[(b'GREATER_THAN', b'GREATER_THAN'), (b'LESS_THAN', b'LESS_THAN'), (b'EQUALS', b'EQUALS')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Household',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('house_number', models.PositiveIntegerField(verbose_name=b'Household Number')),
                ('physical_address', models.CharField(max_length=200, null=True, verbose_name=b'Structure Address', blank=True)),
                ('registration_channel', models.CharField(max_length=100, choices=[('Ussd Access', 'Ussd Access'), ('Odk Access', 'Odk Access'), ('Web Access', 'Web Access')])),
                ('head_desc', models.CharField(max_length=200)),
                ('head_sex', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HouseholdBatchCompletion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('batch', models.ForeignKey(related_name='batch_completion_households', to='survey.Batch', null=True)),
                ('household', models.ForeignKey(related_name='batch_completion_batches', to='survey.Household', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HouseholdListing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('ea', models.ForeignKey(related_name='household_enumeration_area', to='survey.EnumerationArea', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HouseholdMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('surname', models.CharField(max_length=25, verbose_name=b'Family Name')),
                ('first_name', models.CharField(max_length=25, null=True, verbose_name=b'First Name', blank=True)),
                ('gender', models.BooleanField(default=True, verbose_name=b'Sex', choices=[(1, b'M'), (0, b'F')])),
                ('date_of_birth', models.DateField()),
                ('registration_channel', models.CharField(max_length=100, choices=[('Ussd Access', 'Ussd Access'), ('Odk Access', 'Odk Access'), ('Web Access', 'Web Access')])),
            ],
            options={
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HouseholdHead',
            fields=[
                ('householdmember_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.HouseholdMember')),
                ('occupation', models.CharField(default=b'16', max_length=100, verbose_name=b'Occupation / Main Livelihood')),
                ('level_of_education', models.CharField(default=b'Primary', max_length=100, null=True, verbose_name=b'Highest level of education completed', choices=[(b'Did not attend school', b'Did not attend school'), (b'Nursery', b'Nursery'), (b'Primary', b'Primary'), (b"'O' Level", b"'O' Level"), (b"'A' Level", b"'A' Level"), (b'Tertiary', b'Tertiary'), (b'University', b'University')])),
                ('resident_since', models.DateField(null=True, verbose_name=b'Since when have you lived here', blank=True)),
            ],
            options={
                'verbose_name': 'Main Respondent',
            },
            bases=('survey.householdmember',),
        ),
        migrations.CreateModel(
            name='HouseholdMemberBatchCompletion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('batch', models.ForeignKey(related_name='completed_households', to='survey.Batch', null=True)),
                ('householdmember', models.ForeignKey(related_name='completed_member_batches', to='survey.HouseholdMember', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HouseholdMemberGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=50)),
                ('order', models.PositiveIntegerField(default=0, unique=True, max_length=5)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HouseMemberSurveyCompletion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('householdmember', models.ForeignKey(related_name='completion_register', to='survey.HouseholdMember', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HouseSurveyCompletion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('household', models.ForeignKey(related_name='completion_registry', to='survey.Household', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImageAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/mics/answerFiles')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Indicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(null=True)),
                ('measure', models.CharField(default=b'Percentage', max_length=255, choices=[(b'%', b'Percentage'), (b'Number', b'Count')])),
                ('batch', models.ForeignKey(related_name='indicators', to='survey.Batch', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('closure_date', models.DateTimeField(null=True, editable=False, blank=True)),
                ('batch', models.ForeignKey(related_name='interviews', to='survey.Batch')),
                ('ea', models.ForeignKey(related_name='interviews', to='survey.EnumerationArea')),
                ('householdmember', models.ForeignKey(related_name='interviews', to='survey.HouseholdMember', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Interviewer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=100)),
                ('gender', models.CharField(default=b'1', max_length=10, verbose_name=b'Sex', choices=[(b'1', b'M'), (b'0', b'F')])),
                ('date_of_birth', models.DateField(null=True, validators=[survey.models.interviewer.validate_min_date_of_birth, survey.models.interviewer.validate_max_date_of_birth])),
                ('level_of_education', models.CharField(default=b'Primary', max_length=100, null=True, verbose_name=b'Highest level of education completed', choices=[(b'Did not attend school', b'Did not attend school'), (b'Nursery', b'Nursery'), (b'Primary', b'Primary'), (b"'O' Level", b"'O' Level"), (b"'A' Level", b"'A' Level"), (b'Tertiary', b'Tertiary'), (b'University', b'University')])),
                ('is_blocked', models.BooleanField(default=False)),
                ('language', models.CharField(default=b'English', max_length=100, null=True, verbose_name=b'Preferred language of communication', choices=[(b'English', b'English'), (b'Luganda', b'Luganda'), (b'Runyankore-Rukiga', b'Runyankore-Rukiga'), (b'Runyoro-Rutoro', b'Runyoro-Rutoro'), (b'Swahili', b'Swahili'), (b'Ateso-Karimojong', b'Ateso-Karimojong'), (b'Luo', b'Luo'), (b'Lugbara', b'Lugbara')])),
                ('weights', models.FloatField(default=0)),
                ('ea', models.ForeignKey(related_name='interviewers', verbose_name=b'Enumeration Area', to='survey.EnumerationArea', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InterviewerAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('user_identifier', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True, verbose_name=b'Activated')),
                ('reponse_timeout', models.PositiveIntegerField(default=1000, help_text=b'Max time to wait for response before ending interview', null=True, blank=True)),
                ('duration', models.CharField(default=b'H', max_length=100, null=True, blank=True, choices=[(b'D', b'Days'), (b'H', b'Hours'), (b'M', b'Minutes'), (b'S', b'Seconds')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=50)),
                ('code', models.CharField(max_length=100, null=True, blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('location_code', models.PositiveIntegerField(null=True, blank=True)),
                ('slug', models.SlugField()),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='sub_types', blank=True, to='survey.LocationType', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocationTypeDetails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('required', models.BooleanField(default=False, verbose_name=b'required')),
                ('has_code', models.BooleanField(default=False, verbose_name=b'has code')),
                ('length_of_code', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ('order', models.PositiveIntegerField(unique=True, null=True, blank=True)),
                ('country', models.ForeignKey(related_name='details', to='survey.Location', null=True)),
                ('location_type', models.ForeignKey(related_name='details', to='survey.LocationType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocationWeight',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('selection_probability', models.FloatField(default=1.0)),
                ('location', models.ForeignKey(related_name='weight', to='survey.Location')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiChoiceAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('interview', models.ForeignKey(related_name='multichoiceanswer', to='survey.Interview')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiSelectAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('interview', models.ForeignKey(related_name='multiselectanswer', to='survey.Interview')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NonResponseAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.CharField(max_length=100)),
                ('household', models.ForeignKey(related_name='non_response_answers', to='survey.Household')),
                ('interviewer', models.ForeignKey(related_name='non_response_answers', to='survey.Interviewer', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NumericalAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.PositiveIntegerField(max_length=5, null=True)),
                ('interview', models.ForeignKey(related_name='numericalanswer', to='survey.Interview')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ODKAccess',
            fields=[
                ('intervieweraccess_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.InterviewerAccess')),
                ('odk_token', models.CharField(default=b'12345', max_length=10)),
            ],
            options={
            },
            bases=('survey.intervieweraccess',),
        ),
        migrations.CreateModel(
            name='ODKGeoPoint',
            fields=[
                ('point_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='locations.Point')),
                ('altitude', models.DecimalField(max_digits=10, decimal_places=3)),
                ('precision', models.DecimalField(max_digits=10, decimal_places=3)),
            ],
            options={
                'abstract': False,
            },
            bases=('locations.point',),
        ),
        migrations.CreateModel(
            name='ODKSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('form_id', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256, null=True, blank=True)),
                ('instance_id', models.CharField(max_length=256)),
                ('xml', models.TextField()),
                ('household', models.ForeignKey(related_name='odk_submissions', blank=True, to='survey.Household', null=True)),
                ('household_member', models.ForeignKey(related_name='odk_submissions', blank=True, to='survey.HouseholdMember', null=True)),
                ('interviewer', models.ForeignKey(related_name='odk_submissions', to='survey.Interviewer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('identifier', models.CharField(max_length=100, null=True, verbose_name=b'Variable Name')),
                ('text', models.CharField(max_length=150)),
                ('answer_type', models.CharField(max_length=100, choices=[('Numerical Answer', 'Numerical Answer'), ('Text Answer', 'Text Answer'), ('Multi Choice Answer', 'Multi Choice Answer'), ('Multi Select Answer', 'Multi Select Answer'), ('Date Answer', 'Date Answer'), ('Audio Answer', 'Audio Answer'), ('Video Answer', 'Video Answer'), ('Image Answer', 'Image Answer'), ('Geopoint Answer', 'Geopoint Answer')])),
                ('batch', models.ForeignKey(related_name='batch_questions', to='survey.Batch')),
                ('group', models.ForeignKey(related_name='questions', to='survey.HouseholdMemberGroup')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionFlow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('validation_test', models.CharField(blank=True, max_length=200, null=True, choices=[(b'starts_with', b'starts_with'), (b'ends_with', b'ends_with'), (b'equals', b'equals'), (b'between', b'between'), (b'less_than', b'less_than'), (b'greater_than', b'greater_than'), (b'contains', b'contains')])),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('desc', models.CharField(max_length=200, null=True, blank=True)),
                ('next_question', models.ForeignKey(related_name='connecting_flows', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='survey.Question', null=True)),
                ('question', models.ForeignKey(related_name='flows', to='survey.Question')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('text', models.CharField(max_length=150)),
                ('order', models.PositiveIntegerField()),
                ('question', models.ForeignKey(related_name='options', to='survey.Question', null=True)),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('identifier', models.CharField(max_length=100, unique=True, null=True)),
                ('text', models.CharField(max_length=150)),
                ('answer_type', models.CharField(max_length=100, choices=[('Numerical Answer', 'Numerical Answer'), ('Text Answer', 'Text Answer'), ('Multi Choice Answer', 'Multi Choice Answer'), ('Multi Select Answer', 'Multi Select Answer'), ('Date Answer', 'Date Answer'), ('Audio Answer', 'Audio Answer'), ('Video Answer', 'Video Answer'), ('Image Answer', 'Image Answer'), ('Geopoint Answer', 'Geopoint Answer')])),
                ('group', models.ForeignKey(related_name='question_templates', to='survey.HouseholdMemberGroup')),
                ('module', models.ForeignKey(related_name='question_templates', to='survey.QuestionModule')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RandomSelection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('household', models.OneToOneField(related_name='random_selection', to='survey.Household')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=100, unique=True, null=True)),
                ('description', models.CharField(max_length=300, null=True, blank=True)),
                ('sample_size', models.PositiveIntegerField(default=10, max_length=2)),
                ('has_sampling', models.BooleanField(default=True, verbose_name=b'Survey Type')),
                ('preferred_listing', models.ForeignKey(related_name='householdlist_users', blank=True, to='survey.Survey', help_text=b'Select which survey household listing to reuse. Leave empty for fresh listing', null=True)),
            ],
            options={
                'ordering': ['name'],
                'permissions': (('view_completed_survey', 'Can view Completed interviewers'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SurveyAllocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('stage', models.CharField(blank=True, max_length=20, null=True, choices=[(1, b'LISTING'), (2, b'SURVEY')])),
                ('status', models.IntegerField(default=0, choices=[(0, b'PENDING'), (2, b'DEALLOCATED'), (1, b'COMPLETED')])),
                ('allocation_ea', models.ForeignKey(related_name='survey_allocations', to='survey.EnumerationArea')),
                ('interviewer', models.ForeignKey(related_name='assignments', to='survey.Interviewer')),
                ('survey', models.ForeignKey(related_name='work_allocation', to='survey.Survey')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SurveyHouseholdListing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('listing', models.ForeignKey(related_name='survey_houselistings', to='survey.HouseholdListing')),
                ('survey', models.ForeignKey(related_name='survey_house_listings', to='survey.Survey')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TemplateOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('text', models.CharField(max_length=150)),
                ('order', models.PositiveIntegerField()),
                ('question', models.ForeignKey(related_name='options', to='survey.QuestionTemplate', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestArgument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position', models.PositiveIntegerField()),
            ],
            options={
                'get_latest_by': 'position',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NumberArgument',
            fields=[
                ('testargument_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.TestArgument')),
                ('param', models.IntegerField()),
            ],
            options={
            },
            bases=('survey.testargument',),
        ),
        migrations.CreateModel(
            name='DateArgument',
            fields=[
                ('testargument_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.TestArgument')),
                ('param', models.DateField()),
            ],
            options={
            },
            bases=('survey.testargument',),
        ),
        migrations.CreateModel(
            name='TextAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.CharField(max_length=100)),
                ('interview', models.ForeignKey(related_name='textanswer', to='survey.Interview')),
                ('question', models.ForeignKey(related_name='textanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextArgument',
            fields=[
                ('testargument_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.TestArgument')),
                ('param', models.TextField()),
            ],
            options={
            },
            bases=('survey.testargument',),
        ),
        migrations.CreateModel(
            name='UploadErrorLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('model', models.CharField(max_length=20, null=True)),
                ('filename', models.CharField(max_length=20, null=True, blank=True)),
                ('row_number', models.PositiveIntegerField(null=True, blank=True)),
                ('error', models.CharField(max_length=200, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('mobile_number', models.CharField(unique=True, max_length=10, validators=[django.core.validators.MinLengthValidator(9), django.core.validators.MaxLengthValidator(9)])),
                ('user', models.OneToOneField(related_name='userprofile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='USSDAccess',
            fields=[
                ('intervieweraccess_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.InterviewerAccess')),
                ('aggregator', models.CharField(default=b'testAggregator', max_length=100, null=True, blank=True, choices=[(b'testAggregator', b'testAggregator')])),
            ],
            options={
            },
            bases=('survey.intervieweraccess',),
        ),
        migrations.CreateModel(
            name='VideoAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('value', models.FileField(null=True, upload_to=b'/home/anthony/workspace/uSurvey/mics/answerFiles')),
                ('interview', models.ForeignKey(related_name='videoanswer', to='survey.Interview')),
                ('question', models.ForeignKey(related_name='videoanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WebAccess',
            fields=[
                ('intervieweraccess_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='survey.InterviewerAccess')),
            ],
            options={
            },
            bases=('survey.intervieweraccess',),
        ),
        migrations.AddField(
            model_name='testargument',
            name='flow',
            field=models.ForeignKey(related_name='"testargument"', to='survey.QuestionFlow'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='randomselection',
            name='survey',
            field=models.ForeignKey(related_name='random_selections', to='survey.Survey'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='module',
            field=models.ForeignKey(related_name='questions', default=b'', to='survey.QuestionModule'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('identifier', 'batch')]),
        ),
        migrations.AddField(
            model_name='odksubmission',
            name='survey',
            field=models.ForeignKey(related_name='odk_submissions', to='survey.Survey'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='numericalanswer',
            name='question',
            field=models.ForeignKey(related_name='numericalanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nonresponseanswer',
            name='survey_listing',
            field=models.ForeignKey(related_name='non_response_answers', to='survey.SurveyHouseholdListing'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multiselectanswer',
            name='question',
            field=models.ForeignKey(related_name='multiselectanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multiselectanswer',
            name='value',
            field=models.ManyToManyField(to='survey.QuestionOption', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multichoiceanswer',
            name='question',
            field=models.ForeignKey(related_name='multichoiceanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multichoiceanswer',
            name='value',
            field=models.ForeignKey(to='survey.QuestionOption', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='locationweight',
            name='survey',
            field=models.ForeignKey(related_name='location_weight', to='survey.Survey'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='coordinates',
            field=models.ManyToManyField(related_name='admin_div_locations', to='locations.Point'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='sub_locations', blank=True, to='survey.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='type',
            field=models.ForeignKey(related_name='locations', to='survey.LocationType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='intervieweraccess',
            name='interviewer',
            field=models.ForeignKey(related_name='intervieweraccess', to='survey.Interviewer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interview',
            name='interview_channel',
            field=models.ForeignKey(related_name='interviews', to='survey.InterviewerAccess'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interview',
            name='interviewer',
            field=models.ForeignKey(related_name='interviews', to='survey.Interviewer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interview',
            name='last_question',
            field=models.ForeignKey(related_name='ongoing', blank=True, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='interview',
            unique_together=set([('householdmember', 'batch')]),
        ),
        migrations.AddField(
            model_name='indicator',
            name='module',
            field=models.ForeignKey(related_name='indicator', to='survey.QuestionModule'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='imageanswer',
            name='interview',
            field=models.ForeignKey(related_name='imageanswer', to='survey.Interview'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='imageanswer',
            name='question',
            field=models.ForeignKey(related_name='imageanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='housesurveycompletion',
            name='interviewer',
            field=models.ForeignKey(related_name='house_completion', to='survey.Interviewer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='housesurveycompletion',
            name='survey',
            field=models.ForeignKey(related_name='house_completion', to='survey.Survey'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='housemembersurveycompletion',
            name='interviewer',
            field=models.ForeignKey(related_name='house_member_completion', to='survey.Interviewer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='housemembersurveycompletion',
            name='survey',
            field=models.ForeignKey(related_name='completion_register', to='survey.Survey'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='householdmemberbatchcompletion',
            name='interviewer',
            field=models.ForeignKey(related_name='completed_batches', to='survey.Interviewer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='householdmember',
            name='household',
            field=models.ForeignKey(related_name='household_members', to='survey.Household'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='householdmember',
            name='registrar',
            field=models.ForeignKey(related_name='registered_household_members', to='survey.Interviewer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='householdmember',
            name='survey_listing',
            field=models.ForeignKey(related_name='house_members', to='survey.SurveyHouseholdListing'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='householdlisting',
            name='initial_survey',
            field=models.ForeignKey(related_name='listings', to='survey.Survey'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='householdlisting',
            name='list_registrar',
            field=models.ForeignKey(related_name='listings', verbose_name=b'Interviewer', to='survey.Interviewer'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='householdlisting',
            unique_together=set([('initial_survey', 'ea')]),
        ),
        migrations.AddField(
            model_name='householdbatchcompletion',
            name='interviewer',
            field=models.ForeignKey(related_name='batch_completed_households', to='survey.Interviewer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='household',
            name='last_registrar',
            field=models.ForeignKey(related_name='registered_households', verbose_name=b'Interviewer', to='survey.Interviewer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='household',
            name='listing',
            field=models.ForeignKey(related_name='households', to='survey.HouseholdListing'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='household',
            unique_together=set([('house_number', 'listing')]),
        ),
        migrations.AddField(
            model_name='groupcondition',
            name='groups',
            field=models.ManyToManyField(related_name='conditions', to='survey.HouseholdMemberGroup'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='groupcondition',
            unique_together=set([('value', 'attribute', 'condition')]),
        ),
        migrations.AddField(
            model_name='geopointanswer',
            name='interview',
            field=models.ForeignKey(related_name='geopointanswer', to='survey.Interview'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='geopointanswer',
            name='question',
            field=models.ForeignKey(related_name='geopointanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='geopointanswer',
            name='value',
            field=models.ForeignKey(to='survey.ODKGeoPoint', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formula',
            name='count',
            field=models.ForeignKey(related_name='as_count', blank=True, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formula',
            name='denominator',
            field=models.ForeignKey(related_name='as_denominator', blank=True, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formula',
            name='denominator_options',
            field=models.ManyToManyField(related_name='denominator_options', null=True, to='survey.QuestionOption', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formula',
            name='groups',
            field=models.ForeignKey(related_name='as_group', blank=True, to='survey.HouseholdMemberGroup', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formula',
            name='indicator',
            field=models.ForeignKey(related_name='formula', to='survey.Indicator', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formula',
            name='numerator',
            field=models.ForeignKey(related_name='as_numerator', to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formula',
            name='numerator_options',
            field=models.ManyToManyField(related_name='numerator_options', null=True, to='survey.QuestionOption', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='enumerationarea',
            name='locations',
            field=models.ManyToManyField(related_name='enumeration_areas', null=True, to='survey.Location'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dateanswer',
            name='interview',
            field=models.ForeignKey(related_name='dateanswer', to='survey.Interview'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dateanswer',
            name='question',
            field=models.ForeignKey(related_name='dateanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='batchlocationstatus',
            name='location',
            field=models.ForeignKey(related_name='open_batches', to='survey.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='batchcommencement',
            name='ea',
            field=models.ForeignKey(related_name='commencement_registry', to='survey.EnumerationArea', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='batchcommencement',
            name='survey',
            field=models.ForeignKey(related_name='commencement_registry', to='survey.Survey', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='batchchannel',
            unique_together=set([('batch', 'channel')]),
        ),
        migrations.AddField(
            model_name='batch',
            name='start_question',
            field=models.OneToOneField(related_name='starter_batch', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='survey.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='batch',
            name='survey',
            field=models.ForeignKey(related_name='batches', to='survey.Survey', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='batch',
            unique_together=set([('survey', 'name')]),
        ),
        migrations.AddField(
            model_name='audioanswer',
            name='interview',
            field=models.ForeignKey(related_name='audioanswer', to='survey.Interview'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='audioanswer',
            name='question',
            field=models.ForeignKey(related_name='audioanswer', on_delete=django.db.models.deletion.PROTECT, to='survey.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attachment',
            name='submission',
            field=models.ForeignKey(related_name='attachments', to='survey.ODKSubmission'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='answeraccessdefinition',
            unique_together=set([('answer_type', 'channel')]),
        ),
    ]
