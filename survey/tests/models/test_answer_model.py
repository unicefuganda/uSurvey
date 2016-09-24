from django.test import TestCase
from survey.models import EnumerationArea

from survey.models.batch import Batch
from survey.models.backend import Backend
from survey.models.households import Household, HouseholdListing, HouseholdMember, SurveyHouseholdListing
from survey.models.interviewer import Interviewer
from survey.models.surveys import Survey
from survey.models.questions import Question, QuestionOption
from survey.models.question_module import QuestionModule
from survey.models.householdgroups import HouseholdMemberGroup
from survey.models.interviews import NumericalAnswer, TextAnswer, MultiChoiceAnswer, Interview
from survey.models.access_channels import InterviewerAccess, ODKAccess


class NumericalAnswerTest(TestCase):

    def test_store(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")
        household_member_group = HouseholdMemberGroup.objects.create(
            name="test name", order=1)
        question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        batch = Batch.objects.create(order=1)
        question = Question.objects.create(identifier='1.1', text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group, batch=batch, module=question_mod)
        interviewer_access = InterviewerAccess.objects.create(interviewer=investigator, user_identifier="test", is_active=True,
                                                              reponse_timeout=100, duration="120")
        odk_access = ODKAccess.objects.create(interviewer=investigator, user_identifier="test", is_active=True,
                                              reponse_timeout=100, duration="120", odk_token="test123")
        interview = Interview.objects.create(interviewer=investigator, householdmember=household_member, batch=batch,
                                             interview_channel=interviewer_access, closure_date="2017-01-01", ea=ea, last_question=question)
        answer = NumericalAnswer.objects.create(interview=interview, question=question,
                                                value=10)
        self.failUnless(answer.id)


class TextAnswerTest(TestCase):

    def test_store(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")
        household_member_group = HouseholdMemberGroup.objects.create(
            name="test name", order=1)
        question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        batch = Batch.objects.create(order=1)
        question = Question.objects.create(identifier='1.1', text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group, batch=batch, module=question_mod)
        interviewer_access = InterviewerAccess.objects.create(interviewer=investigator, user_identifier="test", is_active=True,
                                                              reponse_timeout=100, duration="120")
        odk_access = ODKAccess.objects.create(interviewer=investigator, user_identifier="test", is_active=True,
                                              reponse_timeout=100, duration="120", odk_token="test123")
        interview = Interview.objects.create(interviewer=investigator, householdmember=household_member, batch=batch,
                                             interview_channel=interviewer_access, closure_date="2017-01-01", ea=ea, last_question=question)
        answer = TextAnswer.objects.create(interview=interview, question=question,
                                           value="This is an answer")
        self.failUnless(answer.id)


class MultiChoiceAnswerTest(TestCase):

    def test_store(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")
        household_member_group = HouseholdMemberGroup.objects.create(
            name="test name", order=1)
        question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        batch = Batch.objects.create(order=1)
        question = Question.objects.create(identifier='1.1', text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group, batch=batch, module=question_mod)
        interviewer_access = InterviewerAccess.objects.create(interviewer=investigator, user_identifier="test", is_active=True,
                                                              reponse_timeout=100, duration="120")
        odk_access = ODKAccess.objects.create(interviewer=investigator, user_identifier="test", is_active=True,
                                              reponse_timeout=100, duration="120", odk_token="test123")
        interview = Interview.objects.create(interviewer=investigator, householdmember=household_member, batch=batch,
                                             interview_channel=interviewer_access, closure_date="2017-01-01", ea=ea, last_question=question)
        option1 = QuestionOption.objects.create(
            question=question, text="This is an option1", order=1)
        option2 = QuestionOption.objects.create(
            question=question, text="This is an option2", order=2)

        answer = MultiChoiceAnswer.objects.create(interview=interview, question=question,
                                                  value=option1)
        self.failUnless(answer.id)
