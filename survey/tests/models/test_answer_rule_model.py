# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date
from django.test import TestCase
# from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.locations import LocationType, Location
#from survey.models import Interviewer, Backend, HouseholdMemberGroup, GroupCondition, Household, Batch, NumericalAnswer, Question, AnswerRule, QuestionOption, MultiChoiceAnswer, Answer, EnumerationArea
from survey.models import Interviewer, Backend, HouseholdMemberGroup, SurveyHouseholdListing,GroupCondition, Household, Batch, NumericalAnswer, Question, QuestionOption, MultiChoiceAnswer, Answer, EnumerationArea, HouseholdListing
from survey.models.surveys import Survey
# from survey.models.batch_question_order import BatchQuestionOrder
from survey.models.households import HouseholdMember
from survey.models.question_module import QuestionModule
#Eswar removed AnswerRule as model not available

#Eswar need to look at it completely
class AnswerRuleTest(TestCase):

    def setUp(self):
        self.location_type_country = LocationType.objects.create(name="Country", slug='country')
        self.location_type_district = LocationType.objects.create(name="District", parent=self.location_type_country,slug='district')
        self.location_type_county = LocationType.objects.create(name="County", parent=self.location_type_district,slug='county')
        self.location_type_subcounty = LocationType.objects.create(name="SubCounty", parent=self.location_type_county,slug='subcounty')
        self.location_type_parish = LocationType.objects.create(name="Parish", parent=self.location_type_subcounty,slug='parish')
        self.location_type_village = LocationType.objects.create(name="Village", parent=self.location_type_parish,slug='village')
        self.location = Location.objects.create(name="Kampala", type=self.location_type_country, code=256
                                                )
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        #ea.locations.add(self.location)
        self.investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)

        self.member_group = HouseholdMemberGroup.objects.create(name="test name", order=1)
        self.condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)
        survey = Survey.objects.create(name="Test Survey",description="Desc",sample_size=10,has_sampling=True)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=survey)
        self.household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        self.question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=survey)
        self.household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=self.household,survey_listing=survey_householdlisting,
                                                          registrar=self.investigator,registration_channel="ODK Access")
        self.batch = Batch.objects.create(order=1)
        self.batch.open_for_location(self.location)

    # def test_numerical_equals_and_end_rule(self):
    #     NumericalAnswer.objects.all().delete()
    #     household_member_group = HouseholdMemberGroup.objects.create(name="test name2", order=2)
    #     question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
    #     batch = Batch.objects.create(order=1)
    #     question_1 = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
    #                                        group=household_member_group,batch=batch,module=question_mod)
    #     question_2 = Question.objects.create(identifier='1.2',text="How many of them are male?",
    #                                          answer_type="Numerical Answer", group=household_member_group,batch=batch,
    #                                          module=question_mod)
    #     # question_1.batches.add(self.batch)
    #     # question_2.batches.add(self.batch)
    #
    #     # BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=1)
    #     # BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=1, batch=self.batch)
    #     # self.assertEqual(next_question, question_2)
    #
    #     NumericalAnswer.objects.all().delete()
    #     # AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'],
    #     #                           condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=0, batch=self.batch)
    #     self.assertEqual(next_question, question_1)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=0, batch=self.batch)
    #     self.assertEqual(next_question, None)
    #
    # def test_numerical_equals_and_skip_to_rule(self):
    #     NumericalAnswer.objects.all().delete()
    #     question_1 = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
    #                                        group=self.member_group,batch=self.batch,module=question_mod)
    #     question_2 = Question.objects.create(text="Question 2?",
    #                                          answer_type=Question.NUMBER, order=2, group=self.member_group)
    #     question_3 = Question.objects.create(text="Question 3?",
    #                                          answer_type=Question.NUMBER, order=3, group=self.member_group)
    #     question_1.batches.add(self.batch)
    #     question_2.batches.add(self.batch)
    #     question_3.batches.add(self.batch)
    #
    #     # BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=1)
    #     # BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)
    #     # BatchQuestionOrder.objects.create(question=question_3, batch=self.batch, order=3)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=1, batch=self.batch)
    #     self.assertEqual(next_question, question_2)
    #
    #     NumericalAnswer.objects.all().delete()
    #     # AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['SKIP_TO'],
    #     #                                  condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0,
    #     #                                  next_question=question_3)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=0, batch=self.batch)
    #     self.assertEqual(next_question, question_3)

    # def test_numerical_greater_than_value_and_reanswer(self):
    #     NumericalAnswer.objects.all().delete()
    #     question_0 = Question.objects.create( text="How are you?", answer_type=Question.NUMBER,
    #                                          order=0, group=self.member_group)
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #     # AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['REANSWER'],
    #     #                                  condition=AnswerRule.CONDITIONS['GREATER_THAN_VALUE'], validate_with_value=4)
    #
    #     question_1.batches.add(self.batch)
    #     question_0.batches.add(self.batch)
    #
    #     BatchQuestionOrder.objects.create(question=question_0, batch=self.batch, order=1)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=2)
    #
    #
    #     self.investigator.member_answered(question_0, self.household_member, answer=5, batch=self.batch)
    #
    #     self.assertEqual(NumericalAnswer.objects.count(), 1)
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=5, batch=self.batch)
    #     self.assertEqual(next_question, question_1)
    #     self.assertEqual(NumericalAnswer.objects.count(), 1)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=4, batch=self.batch)
    #     self.assertEqual(next_question, None)
    #     self.assertEqual(NumericalAnswer.objects.count(), 2)
    #
    # def test_numerical_greater_than_question_and_reanswer(self):
    #     NumericalAnswer.objects.all().delete()
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #     question_2 = Question.objects.create(text="How many of them are male?",
    #                                          answer_type=Question.NUMBER, order=2, group=self.member_group)
    #     question_3 = Question.objects.create(text="How many of them are children?",
    #                                          answer_type=Question.NUMBER, order=3, group=self.member_group)
    #     question_1.batches.add(self.batch)
    #     question_2.batches.add(self.batch)
    #     question_3.batches.add(self.batch)
    #
    #     BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=1)
    #     BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)
    #     BatchQuestionOrder.objects.create(question=question_3, batch=self.batch, order=3)
    #
    #     # rule = AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['REANSWER'],
    #     #                                  condition=AnswerRule.CONDITIONS['GREATER_THAN_QUESTION'],
    #     #                                  validate_with_question=question_1)
    #
    #     self.assertEqual(NumericalAnswer.objects.count(), 0)
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=1, batch=self.batch)
    #     self.assertEqual(next_question, question_2)
    #     self.assertEqual(NumericalAnswer.objects.count(), 1)
    #
    #     next_question = self.investigator.member_answered(question_2, self.household_member, answer=10, batch=self.batch)
    #     self.assertEqual(next_question, question_1)
    #     self.assertEqual(NumericalAnswer.objects.count(), 0)
    #
    # def test_numerical_less_than_value_and_reanswer(self):
    #     NumericalAnswer.objects.all().delete()
    #     question_0 = Question.objects.create(text="How are you?", answer_type=Question.NUMBER,
    #                                          order=0, group=self.member_group)
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #
    #     question_1.batches.add(self.batch)
    #     question_0.batches.add(self.batch)
    #
    #     BatchQuestionOrder.objects.create(question=question_0, batch=self.batch, order=1)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=2)
    #
    #     #
    #     # AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['REANSWER'],
    #     #                                  condition=AnswerRule.CONDITIONS['LESS_THAN_VALUE'], validate_with_value=4)
    #
    #     self.investigator.member_answered(question_0, self.household_member, answer=5, batch=self.batch)
    #
    #     self.assertEqual(NumericalAnswer.objects.count(), 1)
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=3, batch=self.batch)
    #     self.assertEqual(next_question, question_1)
    #     self.assertEqual(NumericalAnswer.objects.count(), 1)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=4, batch=self.batch)
    #     self.assertEqual(next_question, None)
    #     self.assertEqual(NumericalAnswer.objects.count(), 2)
    #
    # def test_numerical_less_than_question_and_reanswer(self):
    #     NumericalAnswer.objects.all().delete()
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #     question_2 = Question.objects.create(text="How many of them are male?",
    #                                          answer_type=Question.NUMBER, order=2, group=self.member_group)
    #     question_3 = Question.objects.create(text="How many of them are children?",
    #                                          answer_type=Question.NUMBER, order=3, group=self.member_group)
    #
    #     question_1.batches.add(self.batch)
    #     question_2.batches.add(self.batch)
    #     question_3.batches.add(self.batch)
    #
    #     BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=1)
    #     BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)
    #     BatchQuestionOrder.objects.create(question=question_3, batch=self.batch, order=3)
    #
    #
    #     # AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['REANSWER'],
    #     #                                  condition=AnswerRule.CONDITIONS['LESS_THAN_QUESTION'],
    #     #                                  validate_with_question=question_1)
    #
    #     self.assertEqual(NumericalAnswer.objects.count(), 0)
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=10, batch=self.batch)
    #     self.assertEqual(next_question, question_2)
    #     self.assertEqual(NumericalAnswer.objects.count(), 1)
    #
    #     next_question = self.investigator.member_answered(question_2, self.household_member, answer=9, batch=self.batch)
    #     self.assertEqual(next_question, question_1)
    #     self.assertEqual(NumericalAnswer.objects.count(), 0)
    #
    # def test_multichoice_equals_option_and_ask_sub_question(self):
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.MULTICHOICE, order=1, group=self.member_group)
    #     QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
    #     option_1_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)
    #
    #     sub_question_1 = Question.objects.create(text="Specify others", answer_type=Question.TEXT,
    #                                              subquestion=True, parent=question_1, group=self.member_group)
    #
    #     question_2 = Question.objects.create(text="How many of them are male?",
    #                                          answer_type=Question.NUMBER, order=2, group=self.member_group)
    #
    #     order = 1
    #     for question in [question_1, question_2, sub_question_1]:
    #         BatchQuestionOrder.objects.create(question=question, batch=self.batch, order=order)
    #         self.batch.questions.add(question)
    #         order += 1
    #
    #     # AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
    #     #                                  condition=AnswerRule.CONDITIONS['EQUALS_OPTION'],
    #     #                                  validate_with_option=option_1_2, next_question=sub_question_1)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=1, batch=self.batch)
    #     self.assertEqual(next_question, question_2)
    #
    #     MultiChoiceAnswer.objects.all().delete()
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=2, batch=self.batch)
    #     self.assertEqual(next_question, sub_question_1)
    #     next_question = self.investigator.member_answered(sub_question_1, self.household_member, answer="Some explanation", batch=self.batch)
    #     self.assertEqual(next_question, question_2)
    #
    # def test_should_add_between_condition(self):
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #
    #     # rule = AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'],
    #     #                                  condition=AnswerRule.CONDITIONS['BETWEEN'],
    #     #                                  validate_with_min_value=1, validate_with_max_value=10)
    #     # self.failUnless(rule)
    #     self.batch.questions.add(question_1)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=self.batch, order=1)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=4, batch=self.batch)
    #     self.assertEqual(next_question, question_1)
    #
    #     next_question = self.investigator.member_answered(question_1, self.household_member, answer=4, batch=self.batch)
    #     self.assertIsNone(next_question)
    #
    # def test_end_interview_is_none_if_answer_rule_already_applied_and_same_answer(self):
    #     question_1 = Question.objects.create(text="Question 1?",
    #                                          answer_type=Question.NUMBER, order=10, group=self.member_group)
    #
    #     # rule = AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'],
    #     #                                  condition=AnswerRule.CONDITIONS['LESS_THAN_VALUE'],
    #     #                                  validate_with_value=10)
    #     # answer = NumericalAnswer.objects.create(investigator=self.investigator, household=self.household,
    #     #                                householdmember=self.household_member, question=question_1, batch=self.batch,
    #     #                                rule_applied=rule, is_old=False, answer=2)
    #     #
    #     # self.assertIsNone(rule.end_interview(self.investigator, answer))