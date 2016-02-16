# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import date
from random import randint

from rapidsms.contrib.locations.models import Location
from survey.models.locations import Location,LocationType
from survey.models import Batch, HouseholdMemberGroup, QuestionModule, HouseholdListing,GroupCondition, Question, Formula, Backend, Interviewer, Household, QuestionOption, Survey, EnumerationArea
from survey.models import HouseholdHead, LocationTypeDetails
from survey.models.households import HouseholdMember, SurveyHouseholdListing
from survey.tests.base_test import BaseTest
from survey.models.question_module import QuestionModule
from survey.models.indicators import Indicator

class FormulaTest(BaseTest):
    def setUp(self):
        self.batch = Batch.objects.create(order=1)
        self.member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)
        household_member_group = HouseholdMemberGroup.objects.create(name="test name2", order=2)
        question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        batch = Batch.objects.create(order=1)
        self.question_1 = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group,batch=batch,module=question_mod)
        self.question_2 = Question.objects.create(identifier='1.2',text="How many of them are male?",
                                             answer_type="Numerical Answer", group=household_member_group,batch=batch,
                                             module=question_mod)
        # self.question_1.batches.add(self.batch)
        # self.question_2.batches.add(self.batch)

    def create_household_member(self, household,survey_name):
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        survey = Survey.objects.create(name=survey_name,description="Desc",sample_size=10,has_sampling=True)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=investigator,initial_survey=survey)
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=survey)
        return HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household,survey_listing=survey_householdlisting,
                                                          registrar=investigator,registration_channel="ODK Access")

    def create_household_head(self, uid, investigator):
        self.household = Household.objects.create(investigator=investigator, ea=investigator.ea,
                                                  uid=uid)
        return HouseholdHead.objects.create(household=self.household, surname="Name " + str(randint(1, 9999)),
                                            date_of_birth="1990-02-09")

    def test_store(self):
        household_member_group = HouseholdMemberGroup.objects.create(name="test name123", order=11)
        option1 = QuestionOption.objects.create(question=self.question_1, text="This is an option1",order=1)
        option2 = QuestionOption.objects.create(question=self.question_2, text="This is an option2",order=2)
        health_module = QuestionModule.objects.create(name="Health")
        batch = Batch.objects.create(name="Batch")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                             module=health_module, batch=batch)
        formula = Formula.objects.create(numerator=self.question_1, groups=household_member_group,denominator=self.question_2,
                                         count=self.question_1, indicator=indicator)
        self.failUnless(formula.id)

    # def test_compute_answer_with_group_as_denominator(self):
    #     survey = Survey.objects.create(name="Sampled Survey")
    #     self.country = LocationType.objects.create(name="Country", slug="country")
    #     self.region = LocationType.objects.create(name="Region", slug="region")
    #     self.district = LocationType.objects.create(name="District", slug='district')
    #
    #     uganda = Location.objects.create(name="Uganda", type=self.country)
    #     #LocationTypeDetails.objects.create(location_type=self.country, country=self.uganda)
    #
    #     kampala = Location.objects.create(name="Kampala", type=self.region, tree_parent=uganda)
    #     abim = Location.objects.create(name="abim", type=self.region, tree_parent=uganda)
    #     ea = EnumerationArea.objects.create(name="EA2")
    #     ea.locations.add(kampala)
    #     ea_2 = EnumerationArea.objects.create(name="EA_ 2")
    #     ea_2.locations.add(abim)
    #
    #     backend = Backend.objects.create(name='something')
    #     investigator = Interviewer.objects.create(name="Investigator",
    #                                                ea=ea,
    #                                                gender='1',level_of_education='Primary',
    #                                                language='English',weights=0)
    #     household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=investigator,initial_survey=survey)
    #     # self.household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
    #     #                                      last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
    #
    #     household_1 = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
    #                                          last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",head_sex="MALE")
    #     household_2 = Household.objects.create(house_number=1234567,listing=household_listing,physical_address='Test address7',
    #                                          last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",head_sex="MALE")
    #
    #     investigator_1 = Interviewer.objects.create(name="Investigator2",
    #                                                ea=ea,
    #                                                gender='1',level_of_education='Primary',
    #                                                language='English',weights=0)
    #
    #     household_3 = Household.objects.create(house_number=1234565,listing=household_listing,physical_address='Test address5',
    #                                          last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",head_sex="MALE")
    #     household_4 = Household.objects.create(house_number=1234560,listing=household_listing,physical_address='Test address0',
    #                                          last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",head_sex="MALE")
    #
    #     household_member_group = HouseholdMemberGroup.objects.create(name="test name132", order=22)
    #     question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
    #     batch = Batch.objects.create(order=1)
    #     question_1 = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
    #                                        group=household_member_group,batch=batch,module=question_mod)
    #
    #     multi_choice_question = Question.objects.create(identifier='14.1',text="This is a question32423", answer_type='Numerical Answer',
    #                                        group=household_member_group,batch=batch,module=question_mod)
    #
    #     multi_choice_option_1 = QuestionOption.objects.create(question=multi_choice_question, text="Yes", order=1)
    #     multi_choice_option_2 = QuestionOption.objects.create(question=multi_choice_question, text="No", order=2)
    #     multi_choice_option_3 = QuestionOption.objects.create(question=multi_choice_question, text="Maybe", order=3)
    #     multi_choice_option_4 = QuestionOption.objects.create(question=multi_choice_question, text="Not Known", order=4)
    #     multi_choice_option_5 = QuestionOption.objects.create(question=multi_choice_question, text="N/A", order=5)
    #     multi_choice_option_6 = QuestionOption.objects.create(question=multi_choice_question, text="Ask", order=6)
    #
    #     formula_numerator_options = [multi_choice_option_1, multi_choice_option_2, multi_choice_option_3]
    #
    #     member_1 = self.create_household_member(household_1,"survey 2")
    #     member_2 = self.create_household_member(household_2, "survey 3")
    #     member_3 = self.create_household_member(household_3, "survey 4")
    #     member_4 = self.create_household_member(household_4, "survey 5")
    #     question_module = QuestionModule.objects.create(name="Question module", description="jkahdkjashdkjhaskjdh")
    #     indicator = Indicator.objects.create(module=question_module,name="sample indicator",description="test descr",
    #                                          measure='Number',batch=batch)
    #     formula = Formula.objects.create(numerator=question_1, groups=household_member_group, denominator=multi_choice_question,
    #                                      count=question_1,indicator=indicator)
    #     another_formula = Formula.objects.create(numerator=multi_choice_question, groups=self.member_group)
    #
    #     [another_formula.numerator_options.add(option) for option in formula_numerator_options]
    #
    #     member_1_answer = 20
    #     member_2_answer = 10
    #     member_3_answer = 40
    #     member_4_answer = 50
    #
    #     investigator_group_members = [member_1, member_2]
    #     investigator_1_group_members = [member_3, member_4]
    #
    #     investigator.member_answered(self.question_1, member_1, member_1_answer, self.batch)
    #     investigator.member_answered(self.question_2, member_1, 200, self.batch)
    #     investigator.member_answered(multi_choice_question, member_1, 1, self.batch)
    #     investigator.member_answered(self.question_1, member_2, member_2_answer, self.batch)
    #     investigator.member_answered(self.question_2, member_2, 100, self.batch)
    #     investigator.member_answered(multi_choice_question, member_2, 2, self.batch)
    #
    #     investigator_1.member_answered(self.question_1, member_3, member_3_answer, self.batch)
    #     investigator_1.member_answered(self.question_2, member_3, 400, self.batch)
    #     investigator_1.member_answered(multi_choice_question, member_3, 3, self.batch)
    #     investigator_1.member_answered(self.question_1, member_4, member_4_answer, self.batch)
    #     investigator_1.member_answered(self.question_2, member_4, 500, self.batch)
    #     investigator_1.member_answered(multi_choice_question, member_4, 4, self.batch)
    #
    #     investigator_numerator_expected = (member_1_answer + member_2_answer)
    #     investigator_denominator_expected = len(investigator_group_members)
    #
    #     investigator_1_numerator_expected = (member_3_answer + member_4_answer)
    #     investigator_1_denominator_expected = len(investigator_1_group_members)
    #
    #     expected_answer = investigator_numerator_expected / investigator_denominator_expected
    #
    #     self.assertEqual(investigator_denominator_expected, formula.denominator_computation(investigator, survey))
    #     self.assertEqual(investigator_numerator_expected, formula.numerator_computation(investigator, self.question_1))
    #     self.assertEqual(expected_answer, formula.compute_for_household_with_sub_options(survey, investigator))
    #
    #     expected_answer = investigator_1_numerator_expected / investigator_1_denominator_expected
    #
    #     self.assertEqual(investigator_1_denominator_expected, formula.denominator_computation(investigator_1, survey))
    #     self.assertEqual(investigator_1_numerator_expected, formula.numerator_computation(investigator_1, self.question_1))
    #     self.assertEqual(expected_answer, formula.compute_for_household_with_sub_options(survey, investigator_1))
    #
    #     investigator_multi_choice_numerator = len([multi_choice_option_1, multi_choice_option_2])
    #
    #     expected_answer = investigator_multi_choice_numerator/investigator_denominator_expected
    #     self.assertEqual(investigator_multi_choice_numerator, another_formula.numerator_computation(investigator,
    #                                                                                                 multi_choice_question))
    #     self.assertEqual(expected_answer, another_formula.compute_for_household_with_sub_options(survey, investigator))
    #
    #     investigator_1_multi_choice_numerator = len([multi_choice_option_3])
    #
    #     expected_answer = investigator_1_multi_choice_numerator/investigator_1_denominator_expected
    #     self.assertEqual(investigator_1_multi_choice_numerator, another_formula.numerator_computation(investigator_1,
    #                                                                                                 multi_choice_question))
    #     self.assertEqual(expected_answer, another_formula.compute_for_household_with_sub_options(survey, investigator_1))

    # def test_compute_answer_with_multichoice_numerator_and_multichoice_denominator(self):
    #     survey = Survey.objects.create(name="Sampled Survey")
    #     uganda = Location.objects.create(name="Uganda")
    #     kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
    #     abim = Location.objects.create(name="Abim", tree_parent=uganda)
    #     backend = Backend.objects.create(name='something')
    #     ea = EnumerationArea.objects.create(name="Kampala EA", survey=survey)
    #     ea.locations.add(kampala)
    #     ea_2 = EnumerationArea.objects.create(name="Abim EA", survey=survey)
    #     ea_2.locations.add(abim)
    #
    #     investigator = Interviewer.objects.create(name="Investigator 1", mobile_number="1", ea=ea,
    #                                                backend=backend, weights=0.3)
    #     household_1 = Household.objects.create(investigator=investigator, survey=survey, uid=1, ea=investigator.ea)
    #     household_2 = Household.objects.create(investigator=investigator, survey=survey, uid=2, ea=investigator.ea)
    #
    #     investigator_1 = Interviewer.objects.create(name="Investigator 2", mobile_number="2", ea=ea_2,
    #                                                  backend=backend, weights=0.9)
    #
    #     household_3 = Household.objects.create(investigator=investigator_1, survey=survey, uid=3, ea=investigator_1.ea)
    #     household_4 = Household.objects.create(investigator=investigator_1, survey=survey, uid=4, ea=investigator_1.ea)
    #
    #     multi_choice_question = Question.objects.create(text="Question 2?", answer_type=Question.MULTICHOICE, order=2,
    #                                                    group=self.member_group)
    #
    #     multi_choice_option_1 = QuestionOption.objects.create(question=multi_choice_question, text="Yes", order=1)
    #     multi_choice_option_2 = QuestionOption.objects.create(question=multi_choice_question, text="No", order=2)
    #     multi_choice_option_3 = QuestionOption.objects.create(question=multi_choice_question, text="Maybe", order=3)
    #     multi_choice_option_4 = QuestionOption.objects.create(question=multi_choice_question, text="Not Known", order=4)
    #     multi_choice_option_5 = QuestionOption.objects.create(question=multi_choice_question, text="N/A", order=5)
    #     multi_choice_option_6 = QuestionOption.objects.create(question=multi_choice_question, text="Ask", order=6)
    #
    #     formula_numerator_options = [multi_choice_option_1, multi_choice_option_2, multi_choice_option_3]
    #     formula_denominator_options = [multi_choice_option_1, multi_choice_option_2, multi_choice_option_3,
    #                                    multi_choice_option_4, multi_choice_option_5, multi_choice_option_6]
    #
    #     member_1 = self.create_household_member(household_1)
    #     member_2 = self.create_household_member(household_2)
    #     member_3 = self.create_household_member(household_3)
    #     member_4 = self.create_household_member(household_4)
    #
    #     another_formula = Formula.objects.create(numerator=multi_choice_question, denominator=multi_choice_question)
    #     another_formula_count = Formula.objects.create(numerator=multi_choice_question, count=multi_choice_question)
    #     formula_denominator = Formula.objects.create(numerator=multi_choice_question, denominator=self.question_1)
    #
    #     [another_formula.numerator_options.add(option) for option in formula_numerator_options]
    #     [another_formula.denominator_options.add(option) for option in formula_denominator_options]
    #
    #     [another_formula_count.numerator_options.add(option) for option in formula_numerator_options]
    #     [another_formula_count.denominator_options.add(option) for option in formula_denominator_options]
    #
    #     [formula_denominator.numerator_options.add(option) for option in formula_numerator_options]
    #
    #     investigator.member_answered(multi_choice_question, member_1, 1, self.batch)
    #     investigator.member_answered(multi_choice_question, member_2, 2, self.batch)
    #     investigator.member_answered(self.question_1, member_1, 10, self.batch)
    #     investigator.member_answered(self.question_1, member_2, 40, self.batch)
    #
    #     investigator_1.member_answered(multi_choice_question, member_3, 3, self.batch)
    #     investigator_1.member_answered(multi_choice_question, member_4, 4, self.batch)
    #
    #     investigator_multi_choice_numerator = len([multi_choice_option_1, multi_choice_option_2])
    #     investigator_1_multi_choice_numerator = len([multi_choice_option_3])
    #
    #     investigator_denominator_expected = 2
    #     investigator_1_denominator_expected = 2
    #
    #     expected_answer = investigator_multi_choice_numerator/investigator_denominator_expected
    #     self.assertEqual(investigator_multi_choice_numerator, another_formula.numerator_computation(investigator,
    #                                                                                                 multi_choice_question))
    #     self.assertEqual(expected_answer, another_formula.compute_for_household_with_sub_options(survey, investigator))
    #     self.assertEqual(expected_answer, another_formula_count.compute_for_household_with_sub_options(survey, investigator))
    #
    #
    #     expected_answer = investigator_1_multi_choice_numerator/investigator_1_denominator_expected
    #     self.assertEqual(investigator_1_multi_choice_numerator, another_formula.numerator_computation(investigator_1,
    #                                                                                                 multi_choice_question))
    #     self.assertEqual(expected_answer, another_formula.compute_for_household_with_sub_options(survey, investigator_1))
    #     self.assertEqual(expected_answer, another_formula_count.compute_for_household_with_sub_options(survey, investigator_1))
    #
    #     expected_answer = investigator_multi_choice_numerator/(10+40)
    #     self.assertEqual(expected_answer, formula_denominator.compute_for_household_with_sub_options(survey, investigator))
    #
    # def test_compute_numerical_answers(self):
    #     uganda = Location.objects.create(name="Uganda")
    #     kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
    #     abim = Location.objects.create(name="Abim", tree_parent=uganda)
    #     backend = Backend.objects.create(name='something')
    #     survey = Survey.objects.create(name="huhu")
    #     ea = EnumerationArea.objects.create(name="EA2", survey=survey)
    #     ea.locations.add(kampala)
    #
    #     ea_2 = EnumerationArea.objects.create(name="EA2", survey=survey)
    #     ea_2.locations.add(abim)
    #
    #     investigator = Interviewer.objects.create(name="Investigator 1", mobile_number="1", ea=ea,
    #                                                backend=backend, weights=0.3)
    #     household_1 = Household.objects.create(investigator=investigator, uid=1, ea=investigator.ea)
    #     household_2 = Household.objects.create(investigator=investigator, uid=2, ea=investigator.ea)
    #
    #     investigator_1 = Interviewer.objects.create(name="Investigator 2", mobile_number="2", ea=ea_2,
    #                                                  backend=backend, weights=0.9)
    #     household_3 = Household.objects.create(investigator=investigator_1, uid=3, ea=investigator_1.ea)
    #     household_4 = Household.objects.create(investigator=investigator_1, uid=4, ea=investigator_1.ea)
    #
    #     member_1 = self.create_household_member(household_1)
    #     member_2 = self.create_household_member(household_2)
    #     member_3 = self.create_household_member(household_3)
    #     member_4 = self.create_household_member(household_4)
    #
    #     formula = Formula.objects.create(numerator=self.question_1, denominator=self.question_2)
    #     investigator.member_answered(self.question_1, member_1, 20, self.batch)
    #     investigator.member_answered(self.question_2, member_1, 200, self.batch)
    #     investigator.member_answered(self.question_1, member_2, 10, self.batch)
    #     investigator.member_answered(self.question_2, member_2, 100, self.batch)
    #
    #     investigator_1.member_answered(self.question_1, member_3, 40, self.batch)
    #     investigator_1.member_answered(self.question_2, member_3, 400, self.batch)
    #     investigator_1.member_answered(self.question_1, member_4, 50, self.batch)
    #     investigator_1.member_answered(self.question_2, member_4, 500, self.batch)
    #
    #     self.assertEquals(formula.compute_for_location(kampala), 3)
    #     self.assertEquals(formula.compute_for_location(abim), 9)
    #     self.assertEquals(formula.compute_for_location(uganda), 6)
    #
    # def test_compute_multichoice_answer(self):
    #     uganda = Location.objects.create(name="Uganda")
    #     kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
    #     abim = Location.objects.create(name="Abim", tree_parent=uganda)
    #     backend = Backend.objects.create(name='something')
    #     survey = Survey.objects.create(name="huhu")
    #     ea = EnumerationArea.objects.create(name="EA2", survey=survey)
    #     ea.locations.add(kampala)
    #     abim_ea = EnumerationArea.objects.create(name="EA2", survey=survey)
    #     abim_ea.locations.add(abim)
    #
    #     investigator = Interviewer.objects.create(name="Investigator 1", mobile_number="1", ea=ea,
    #                                                backend=backend, weights=0.3)
    #     household_1 = Household.objects.create(investigator=investigator, uid=0, ea=investigator.ea)
    #     household_2 = Household.objects.create(investigator=investigator, uid=1, ea=investigator.ea)
    #     household_3 = Household.objects.create(investigator=investigator, uid=2, ea=investigator.ea)
    #
    #     investigator_1 = Interviewer.objects.create(name="Investigator 2", mobile_number="2", ea=abim_ea,
    #                                                  backend=backend, weights=0.9)
    #     household_4 = Household.objects.create(investigator=investigator_1, uid=3, ea=investigator_1.ea)
    #     household_5 = Household.objects.create(investigator=investigator_1, uid=4, ea=investigator_1.ea)
    #     household_6 = Household.objects.create(investigator=investigator_1, uid=5, ea=investigator_1.ea)
    #
    #     member_1 = self.create_household_member(household_1)
    #     member_2 = self.create_household_member(household_2)
    #     member_3 = self.create_household_member(household_3)
    #     member_4 = self.create_household_member(household_4)
    #     member_5 = self.create_household_member(household_5)
    #     member_6 = self.create_household_member(household_6)
    #
    #     self.question_3 = Question.objects.create(text="This is a question",
    #                                               answer_type=Question.MULTICHOICE, order=3, group=self.member_group)
    #     option_1 = QuestionOption.objects.create(question=self.question_3, text="OPTION 2", order=1)
    #     option_2 = QuestionOption.objects.create(question=self.question_3, text="OPTION 1", order=2)
    #
    #     self.question_3.batches.add(self.batch)
    #
    #     formula = Formula.objects.create(numerator=self.question_3, denominator=self.question_1)
    #
    #     investigator.member_answered(self.question_1, member_1, 20, batch=self.batch)
    #     investigator.member_answered(self.question_3, member_1, 1, batch=self.batch)
    #     investigator.member_answered(self.question_1, member_2, 10, batch=self.batch)
    #     investigator.member_answered(self.question_3, member_2, 1, batch=self.batch)
    #     investigator.member_answered(self.question_1, member_3, 30, batch=self.batch)
    #     investigator.member_answered(self.question_3, member_3, 2, batch=self.batch)
    #
    #     investigator_1.member_answered(self.question_1, member_4, 30, batch=self.batch)
    #     investigator_1.member_answered(self.question_3, member_4, 2, batch=self.batch)
    #     investigator_1.member_answered(self.question_1, member_5, 20, batch=self.batch)
    #     investigator_1.member_answered(self.question_3, member_5, 2, batch=self.batch)
    #     investigator_1.member_answered(self.question_1, member_6, 40, batch=self.batch)
    #     investigator_1.member_answered(self.question_3, member_6, 1, batch=self.batch)
    #
    #     self.assertEquals(formula.compute_for_location(kampala), {option_1.text: 15, option_2.text: 15})
    #     self.assertEquals(formula.compute_for_location(abim), {option_1.text: 40, option_2.text: 50})
    #     self.assertEquals(formula.compute_for_location(uganda), {option_1.text: 27.5, option_2.text: 32.5})

    def test_get_group_formula_type(self):
        general_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=21)
        formula = Formula.objects.create(groups=general_group)

        self.assertEqual(general_group, formula.get_count_type())

    def test_get_count_formula_type(self):
        household_member_group = HouseholdMemberGroup.objects.create(name="test name uniq", order=41)
        question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
        batch = Batch.objects.create(order=1)
        question_3 = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group,batch=batch,module=question_mod)
        formula = Formula.objects.create(count=question_3)

        self.assertEqual(question_3, formula.get_count_type())


