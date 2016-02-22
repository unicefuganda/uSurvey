from datetime import date
from random import randint
from django.core.exceptions import ValidationError

from django.test import TestCase
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.locations import LocationType, Location
from survey.models import GroupCondition, HouseholdHead, QuestionModule, Indicator, Formula, Survey, EnumerationArea
from survey.models.batch_question_order import BatchQuestionOrder
from django.db import IntegrityError
from survey.models.batch import Batch
from survey.models.backend import Backend
from survey.models.households import Household, HouseholdMember
from survey.models.interviewer import Interviewer
from survey.models.questions import Question, QuestionOption
from survey.models.householdgroups import HouseholdMemberGroup
from survey.tests.base_test import BaseTest


class QuestionTest(TestCase):
    def setUp(self):
        self.household_member_group = HouseholdMemberGroup.objects.create(name="test name1324", order=12)
        self.question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        self.batch = Batch.objects.create(order=1)

    def test_unicode_representation_of_question(self):
        # household_member_group = HouseholdMemberGroup.objects.create(name="test name132", order=22)
        # question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        # batch = Batch.objects.create(order=1)
        question = Question.objects.create(identifier='123.1',text="This is a question", answer_type='Numerical Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_mod)
        question_unicode = "%s - %s: (%s)" % (question.identifier, question.text, question.answer_type.upper())
        self.assertEqual(question_unicode, str(question))

    def test_numerical_question(self):
        question = Question.objects.create(identifier='13.1',text="This is a question!!!!!!", answer_type='Numerical Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_mod)
        self.failUnless(question.id)

    def test_text_question(self):
        question = Question.objects.create(identifier='23.1',text="This is a question", answer_type='Text Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_mod)
        self.failUnless(question.id)

    def test_variable_name_should_be_unique(self):
        question = Question.objects.create(identifier='143.1',text="This is a question", answer_type='Text Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_mod)
        duplicate_question = Question(identifier='143.1',text="This is a question", answer_type='Text Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_mod)
        self.assertRaises(IntegrityError, duplicate_question.save)

    def test_multichoice_question(self):
        household_member_group = HouseholdMemberGroup.objects.create(name="test name132", order=22)
        question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        batch = Batch.objects.create(order=1)
        question_1 = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group,batch=batch,module=question_mod)

        question = Question.objects.create(identifier='14.1',text="This is a question32423", answer_type='Numerical Answer',
                                           group=household_member_group,batch=batch,module=question_mod)

        multi_choice_option_1 = QuestionOption.objects.create(question=question, text="Yes", order=1)
        multi_choice_option_2 = QuestionOption.objects.create(question=question, text="No", order=2)
        self.failUnless(question.id)

    def test_order(self):
        # question_2 = Question.objects.create(text="This is a question", answer_type="number", order=2)
        # question_1 = Question.objects.create(text="This is another question", answer_type="number",
        #                                      order=1)

        module = QuestionModule.objects.create(name="Health", description="some description")
        household_member_group = HouseholdMemberGroup.objects.create(name="test name2", order=2)
        batch = Batch.objects.create(order=1)
        question_2=Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group,batch=batch,module=module)
        question_1=Question.objects.create(identifier='1.2',text="How many of them are male?",
                                             answer_type="Numerical Answer", group=household_member_group,batch=batch,
                                             module=module)
        questions = Question.objects.all()
        self.assertEqual(questions[0], question_2)
        self.assertEqual(questions[1], question_1)

    # def test_get_next_question_in_batch(self):
    #     country = LocationType.objects.create(name="Country", slug='country')
    #     district = LocationType.objects.create(name="District", parent=country,slug='district')
    #     # county = LocationType.objects.create(name="County", parent=district,slug='county')
    #     # subcounty = LocationType.objects.create(name="SubCounty", parent=county,slug='subcounty')
    #     # parish = LocationType.objects.create(name="Parish", parent=subcounty,slug='parish')
    #     # village = LocationType.objects.create(name="Village", parent=parish,slug='village')
    #
    #     batch = Batch.objects.create(order=1)
    #     uganda = Location.objects.create(name="Uganda", type=country)
    #     kampala = Location.objects.create(name="Kampala", type=district, parent=uganda)
    #
    #     module = QuestionModule.objects.create(name="Health", description="some description")
    #     household_member_group = HouseholdMemberGroup.objects.create(name="test name2", order=2)
    #     question_2=Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
    #                                        group=household_member_group,batch=batch,module=module)
    #     question_1=Question.objects.create(identifier='1.2',text="How many of them are male?",
    #                                          answer_type="Numerical Answer", group=household_member_group,batch=batch,
    #                                          module=module)
    #     self.batch.open_for_location(kampala)
    #     # question_1.batches.add(self.batch)
    #     # question_2.batches.add(self.batch)
    #
    #     print question_2.next_question(kampala),"+++++++++++++++++++++"
    #     self.assertEqual(question_2, question_1.next_question(kampala))
    #
    # def test_get_next_question_in_batch_if_sub_question_is_provided(self):
    #     kampala = Location.objects.create(name="Kampala")
    #     question_2 = Question.objects.create(text="This is a question", answer_type="number", order=2)
    #     question_1 = Question.objects.create(text="This is another question", answer_type="number",
    #                                          order=1)
    #     sub_question_1 = Question.objects.create(text="This is another question", answer_type="number",
    #                                              parent=question_1, subquestion=True)
    #     self.batch.open_for_location(kampala)
    #     question_1.batches.add(self.batch)
    #     question_2.batches.add(self.batch)
    #
    #     self.assertEqual(question_2, sub_question_1.next_question(kampala))
    #
    # def test_cannot_save_subquestion_if_order_given(self):
    #     batch = Batch.objects.create(order=1)
    #     module = QuestionModule.objects.create(name="Health", description="some description")
    #     household_member_group = HouseholdMemberGroup.objects.create(name="test name2", order=2)
    #     question_2=Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
    #                                        group=household_member_group,batch=batch,module=module)
    #     subquestion = Question(text="Specify others", answer_type="Text Answer", subquestion=True, parent=question_2,
    #                            order=1)
    #     self.assertRaises(ValidationError, subquestion.save)
    #
    # def test_cannot_save_subquestion_if_parent_not_given(self):
    #     subquestion = Question(text="Specify others", answer_type=Question.TEXT, subquestion=True)
    #     self.assertRaises(ValidationError, subquestion.save)
    #
    # def test_question_is_subquestion_if_parent_is_given(self):
    #     question_2 = Question.objects.create(text="This is a question", answer_type="number", order=2)
    #     subquestion = Question(text="Specify others", answer_type=Question.TEXT, parent=question_2)
    #     subquestion.save()
    #
    #     self.assertEqual(False, question_2.subquestion)
    #     self.assertEqual(True, subquestion.subquestion)
    #
    # def test_question_should_know_it_all_question_fields(self):
    #     question = Question()
    #
    #     fields = [str(item.attname) for item in question._meta.fields]
    #
    #     for field in ['id', 'identifier', 'group_id', 'text', 'answer_type', 'order', 'subquestion',
    #                   'parent_id', 'created', 'modified', 'module_id']:
    #         self.assertIn(field, fields)
    #
    #     self.assertEqual(len(fields), 11)
    #
    # def test_knows_what_group_question_belongs_to_when_successfully_created(self):
    #     household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)
    #
    #     data = {'identifier': 'question',
    #             'text': "This is a question",
    #             'answer_type': 'number',
    #             'order': 1,
    #             'subquestion': False,
    #             'group': household_member_group}
    #
    #     question = Question.objects.create(**data)
    #
    #     self.assertEqual(household_member_group, question.group)
    #
    # def test_knows_has_been_answered_by_member(self):
    #     backend = Backend.objects.create(name='something')
    #     kampala = Location.objects.create(name="Kampala")
    #     ea = EnumerationArea.objects.create(name="EA2")
    #     ea.locations.add(kampala)
    #
    #     investigator = Interviewer.objects.create(name="", mobile_number="123456789", ea=ea, backend=backend)
    #     household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)
    #
    #     household = Household.objects.create(investigator=investigator, uid=0, ea=investigator.ea)
    #
    #     household_member = HouseholdMember.objects.create(surname="Member",
    #                                                       date_of_birth=date(1980, 2, 2), male=False,
    #                                                       household=household)
    #     household_member_1 = HouseholdMember.objects.create(surname="Member",
    #                                                         date_of_birth=date(1980, 2, 2), male=False,
    #                                                         household=household)
    #
    #     question_1 = Question.objects.create(identifier="identifier1",
    #                                          text="Question 1", answer_type='number',
    #                                          order=1, subquestion=False, group=household_member_group)
    #     self.batch.questions.add(question_1)
    #     self.assertFalse(question_1.has_been_answered(household_member, self.batch))
    #     investigator.member_answered(question_1, household_member, answer=1, batch=self.batch)
    #     self.assertTrue(question_1.has_been_answered(household_member, self.batch))
    #     self.assertFalse(question_1.has_been_answered(household_member_1, self.batch))
    #
    # def test_knows_subquestions_for_a_question(self):
    #     question_1 = Question.objects.create(text="question1", answer_type="number", order=1)
    #     sub_question1 = Question.objects.create(text='sub1', answer_type=Question.NUMBER,
    #                                             subquestion=True, parent=question_1)
    #     sub_question2 = Question.objects.create(text='sub2', answer_type=Question.NUMBER,
    #                                             subquestion=True, parent=question_1)
    #
    #     self.batch.questions.add(question_1)
    #     self.batch.questions.add(sub_question1)
    #     self.batch.questions.add(sub_question2)
    #     subquestions = question_1.get_subquestions()
    #     self.assertIn(sub_question1, subquestions)
    #     self.assertIn(sub_question2, subquestions)
    #
    # def test_question_knows_de_associate_self_from_batch(self):
    #     batch = Batch.objects.create(order=1, name="Test")
    #     batch_question = Question.objects.create(text="This is a test question", answer_type="multichoice")
    #     another_batch_question = Question.objects.create(text="This is another test question",
    #                                                      answer_type=Question.MULTICHOICE)
    #     batch_question.batches.add(batch)
    #     another_batch_question.batches.add(batch)
    #
    #     BatchQuestionOrder.objects.create(question=batch_question, batch=batch, order=1)
    #     BatchQuestionOrder.objects.create(question=another_batch_question, batch=batch, order=2)
    #
    #     batch_question.de_associate_from(batch)
    #
    #     batch_question_order = BatchQuestionOrder.objects.filter(batch=batch, question=batch_question)
    #     self.failIf(batch_question_order)
    #     updated_question = Question.objects.filter(text="This is a test question", answer_type="multichoice",
    #                                                batches=batch)
    #     self.failIf(updated_question)
    #
    #     remaining_batch_order_questions = BatchQuestionOrder.objects.filter(batch=batch,
    #                                                                         question=another_batch_question)
    #     self.failUnless(remaining_batch_order_questions)
    #     self.assertEqual(1, remaining_batch_order_questions[0].order)
    #
    # def test_question_knows_it_belongs_to_agroup(self):
    #     another_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=1)
    #     general_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=2)
    #
    #     general_condition = GroupCondition.objects.create(attribute="GENERAL", value="HEAD", condition='EQUALS')
    #     general_group.conditions.add(general_condition)
    #
    #     general_question = Question.objects.create(group=general_group, text="General Question 1",
    #                                                answer_type=Question.NUMBER,
    #                                                order=4, identifier='Q3')
    #     another_group_question = Question.objects.create(group=another_group, text="General Question 2",
    #                                                      answer_type=Question.NUMBER,
    #                                                      order=5, identifier='Q4')
    #
    #     self.assertTrue(general_question.belongs_to(general_group))
    #     self.assertFalse(general_question.belongs_to(another_group))
    #
    #     self.assertTrue(another_group_question.belongs_to(another_group))
    #     self.assertFalse(another_group_question.belongs_to(general_group))


# class SimpleIndicatorQuestionCount(BaseTest):
#     def create_household_head(self, uid, investigator):
#         self.household = Household.objects.create(investigator=investigator, ea=investigator.ea,
#                                                   uid=uid, survey=self.survey)
#         return HouseholdHead.objects.create(household=self.household, surname="Name " + str(randint(1, 9999)),
#                                             date_of_birth="1990-02-09")
#
#     def setUp(self):
#         self.survey = Survey.objects.create(name="haha")
#         self.batch = Batch.objects.create(order=1, survey=self.survey)
#         self.country = LocationType.objects.create(name="Country", slug="country")
#         self.region = LocationType.objects.create(name="Region", slug="region")
#         self.district = LocationType.objects.create(name="District", slug='district')
#
#         self.uganda = Location.objects.create(name="Uganda", type=self.country)
#         self.west = Location.objects.create(name="WEST", type=self.region, tree_parent=self.uganda)
#         self.central = Location.objects.create(name="CENTRAL", type=self.region, tree_parent=self.uganda)
#         self.kampala = Location.objects.create(name="Kampala", tree_parent=self.central, type=self.district)
#         self.mbarara = Location.objects.create(name="Mbarara", tree_parent=self.west, type=self.district)
#         ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
#         ea.locations.add(self.kampala)
#         mbarara_ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
#         mbarara_ea.locations.add(self.mbarara)
#
#
#         backend = Backend.objects.create(name='something')
#
#         self.investigator = Interviewer.objects.create(name="Investigator 1", mobile_number="1", ea=ea,
#                                                    backend=backend)
#         self.investigator_2 = Interviewer.objects.create(name="Investigator 1", mobile_number="33331", ea=mbarara_ea,
#                                                      backend=backend)
#
#         health_module = QuestionModule.objects.create(name="Health")
#         member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
#         self.question_3 = Question.objects.create(text="This is a question",
#                                                   answer_type=Question.MULTICHOICE, order=3,
#                                                   module=health_module, group=member_group)
#         self.yes_option = QuestionOption.objects.create(question=self.question_3, text="Yes", order=1)
#         self.no_option = QuestionOption.objects.create(question=self.question_3, text="No", order=2)
#
#         self.question_3.batches.add(self.batch)
#
#         self.household_head_1 = self.create_household_head(0, self.investigator)
#         self.household_head_2 = self.create_household_head(1, self.investigator)
#         self.household_head_3 = self.create_household_head(2, self.investigator)
#         self.household_head_4 = self.create_household_head(3, self.investigator)
#         self.household_head_5 = self.create_household_head(4, self.investigator)
#
#         self.household_head_6 = self.create_household_head(5, self.investigator_2)
#         self.household_head_7 = self.create_household_head(6, self.investigator_2)
#         self.household_head_8 = self.create_household_head(7, self.investigator_2)
#         self.household_head_9 = self.create_household_head(8, self.investigator_2)
#
#     def test_returns_options_counts_given_list_of_locations(self):
#         self.investigator.member_answered(self.question_3, self.household_head_1, self.yes_option.order, self.batch)
#         self.investigator.member_answered(self.question_3, self.household_head_2, self.yes_option.order, self.batch)
#         self.investigator.member_answered(self.question_3, self.household_head_3, self.yes_option.order, self.batch)
#         self.investigator.member_answered(self.question_3, self.household_head_4, self.no_option.order, self.batch)
#         self.investigator.member_answered(self.question_3, self.household_head_5, self.no_option.order, self.batch)
#
#         self.investigator_2.member_answered(self.question_3, self.household_head_6, self.yes_option.order, self.batch)
#         self.investigator_2.member_answered(self.question_3, self.household_head_7, self.yes_option.order, self.batch)
#         self.investigator_2.member_answered(self.question_3, self.household_head_8, self.no_option.order, self.batch)
#         self.investigator_2.member_answered(self.question_3, self.household_head_9, self.no_option.order, self.batch)
#
#         region_responses = {self.central: {self.yes_option.text: 3, self.no_option.text: 2},
#                             self.west: {self.yes_option.text: 2, self.no_option.text: 2}}
#         self.assertEquals(self.question_3.hierarchical_result_for(self.uganda, self.survey), region_responses)
#
#         central_region_responses = {self.kampala: {self.yes_option.text: 3, self.no_option.text: 2}}
#         self.assertEquals(self.question_3.hierarchical_result_for(self.central, self.survey), central_region_responses)
#
#         west_region_responses = {self.mbarara: {self.yes_option.text: 2, self.no_option.text: 2}}
#         self.assertEquals(self.question_3.hierarchical_result_for(self.west, self.survey), west_region_responses)
#
#
# class QuestionOptionTest(TestCase):
#     def setUp(self):
#         batch = Batch.objects.create(order=1)
#         self.question = Question.objects.create(text="This is a question", answer_type="multichoice")
#         batch.questions.add(self.question)
#
#     def test_store(self):
#         option_2 = QuestionOption.objects.create(question=self.question, text="OPTION 1", order=2)
#         option_1 = QuestionOption.objects.create(question=self.question, text="OPTION 2", order=1)
#         options = self.question.options.order_by('order').all()
#         self.assertEqual(len(options), 2)
#         options_in_text = "1: %s\n2: %s" % (option_1.text, option_2.text)
#         self.assertEqual(self.question.options_in_text(), options_in_text)
#
#     def test_question_text(self):
#         option_2 = QuestionOption.objects.create(question=self.question, text="OPTION 1", order=2)
#         option_1 = QuestionOption.objects.create(question=self.question, text="OPTION 2", order=1)
#         question_in_text = "%s\n%s" % (self.question.text, self.question.options_in_text())
#         self.assertEqual(self.question.to_ussd(), question_in_text)
