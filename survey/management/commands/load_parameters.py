__author__ = 'anthony'
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from survey.models import AnswerAccessDefinition, NumericalAnswer, TextAnswer, \
    MultiChoiceAnswer, MultiSelectAnswer, ImageAnswer, GeopointAnswer, DateAnswer, AudioAnswer, VideoAnswer, \
    USSDAccess, ODKAccess, WebAccess

class Command(BaseCommand):
    help = 'Creates default parameters'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating permissions....')
        content_type = ContentType.objects.get_for_model(User)
        Permission.objects.get_or_create(codename='can_enter_data', name='Can enter data', content_type=content_type)
        Permission.objects.get_or_create(codename='can_view_batches', name='Can view Batches', content_type=content_type)
        Permission.objects.get_or_create(codename='can_view_interviewers', name='Can view Interviewers', content_type=content_type)
        Permission.objects.get_or_create(codename='can_view_aggregates', name='Can view Aggregates', content_type=content_type)
        Permission.objects.get_or_create(codename='view_completed_survey', name='Can view Completed Surveys', content_type=content_type)
        Permission.objects.get_or_create(codename='can_view_households', name='Can view Households', content_type=content_type)
        Permission.objects.get_or_create(codename='can_view_locations', name='Can view Locations', content_type=content_type)
        Permission.objects.get_or_create(codename='can_view_users', name='Can view Users', content_type=content_type)
        Permission.objects.get_or_create(codename='can_view_household_groups', name='Can view Household Groups', content_type=content_type)

        self.stdout.write('Permissions.')
        self.stdout.write('Creating answer definition... ')
        #ussd definition
        AnswerAccessDefinition.objects.get_or_create(channel=USSDAccess.choice_name(),
                                                     answer_type=NumericalAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=USSDAccess.choice_name(),
                                                     answer_type=TextAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=USSDAccess.choice_name(),
                                                     answer_type=MultiChoiceAnswer.choice_name())

        #ODK definition
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=NumericalAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=TextAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=MultiChoiceAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=MultiSelectAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=ImageAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=GeopointAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=DateAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=AudioAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=ODKAccess.choice_name(),
                                                     answer_type=VideoAnswer.choice_name())

        #web form definition
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=NumericalAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=TextAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=MultiChoiceAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=MultiSelectAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=ImageAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=GeopointAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=DateAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=AudioAnswer.choice_name())
        AnswerAccessDefinition.objects.get_or_create(channel=WebAccess.choice_name(),
                                                     answer_type=VideoAnswer.choice_name())
        self.stdout.write('Successfully imported!')
