from datetime import date
from random import randint

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

    def test_compute_for_next_location_type_in_the_hierarchy(self):
        location_type_country = LocationType.objects.create(name="Country", slug='country')
        location_type_district = LocationType.objects.create(name="District", parent=location_type_country,slug='district')
        uganda = Location.objects.create(name="Uganda", type=location_type_country)
        kampala = Location.objects.create(name="Kampala", parent=uganda, type=location_type_district)
        abim = Location.objects.create(name="Abim", parent=uganda, type=location_type_district)
        backend = Backend.objects.create(name='something')
        survey = Survey.objects.create(name="huhu")
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(kampala)

        ea_2 = EnumerationArea.objects.create(name="EA2")
        ea_2.locations.add(abim)

        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=investigator,initial_survey=survey)
        household_1 = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        household_2 = Household.objects.create(house_number=1234567,listing=household_listing,physical_address='Test address',
                                             last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')

        investigator_1 = Interviewer.objects.create(name="Investigator123",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        household_3 = Household.objects.create(house_number=1234568,listing=household_listing,physical_address='Test address',
                                             last_registrar=investigator_1,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        household_4 = Household.objects.create(house_number=1234569,listing=household_listing,physical_address='Test address',
                                             last_registrar=investigator_1,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')

        household_member_group = HouseholdMemberGroup.objects.create(name="test name1234", order=11)
        health_module = QuestionModule.objects.create(name="Health4")
        batch = Batch.objects.create(name="Batch")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                             module=health_module, batch=batch)

        formula = Formula.objects.create(numerator=self.question_1, groups=household_member_group,denominator=self.question_2,
                                         count=self.question_1, indicator=indicator)
        self.assertEquals(len(formula.compute_for_next_location_type_in_the_hierarchy(kampala)), 0)

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


