__author__ = 'Eswar'

from django.test.client import Client
from django.contrib.auth.models import User
from django.test import TestCase
from survey.models.batch import Batch
from survey.models import GroupCondition, HouseholdHead, QuestionModule, Indicator, Formula, Survey, EnumerationArea, \
    HouseholdMemberGroup, InterviewerAccess, NumericalAnswer

from survey.models.locations import *
from survey.tests.base_test import BaseTest
from survey.odk.utils.odk_helper import *


class ODKHelperTest(TestCase):
    def setUp(self):
        self.question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        self.batch = Batch.objects.create(order=1)
        self.household_member_group = HouseholdMemberGroup.objects.create(name="test name1324", order=12)
        self.ea = EnumerationArea.objects.create(name="EA1")
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.district = LocationType.objects.create(name='District', parent=self.country, slug='district')
        self.survey = Survey.objects.create(name="haha")
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(name="Kampala", type=self.district, parent=self.uganda)
        self.ea.locations.add(self.kampala)
        self.interviewer = Interviewer.objects.create(name="Investigator",
                                                   ea=self.ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        self.question = Question.objects.create(identifier='123.1',text="This is a question", answer_type='Numerical Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_mod)

    def test_get_answer_path(self):
        # question = Question.objects.create(identifier='123.1',text="This is a question", answer_type='Numerical Answer',
        #                                    group=self.household_member_group,batch=self.batch,module=self.question_mod)
        answer_path=get_answer_path(self.batch,self.question)

        expected_result =  '//survey/b%s/q%s' % (self.batch.pk, self.question.pk)
        self.assertEqual(answer_path,expected_result)

    def test_record_interview_answer(self):
        # question = Question.objects.create(identifier='123.2',text="This is a question", answer_type='Numerical Answer',
        #                                    group=self.household_member_group,batch=self.batch,module=self.question_mod)
        survey = Survey.objects.create(name="Test Survey",description="Desc",sample_size=10,has_sampling=True)
        household_listing = HouseholdListing.objects.create(ea=self.ea,list_registrar=self.interviewer,initial_survey=survey)
        household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=self.interviewer,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household,survey_listing=survey_householdlisting,
                                                          registrar=self.interviewer,registration_channel="ODK Access")
        household_member_group = HouseholdMemberGroup.objects.create(name="test name", order=1)
        question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        batch = Batch.objects.create(order=1)
        interviewer_access= InterviewerAccess.objects.create(interviewer=self.interviewer,user_identifier="test",is_active=True,
                                                             reponse_timeout=100,duration="120")
        interview = Interview.objects.create(interviewer=self.interviewer,householdmember=household_member,batch=batch,
                                             interview_channel=interviewer_access,closure_date="2017-01-01",ea=self.ea,last_question=self.question)
        answer = NumericalAnswer.objects.create(interview=interview, question=self.question,
                                                value=1)
        self.assertIsNotNone(record_interview_answer(interview, self.question, 0))
