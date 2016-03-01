from random import randint
from lettuce import *
from rapidsms.contrib.locations.models import *
from survey.models.locations import *
from survey.features.page_objects.indicators import ListIndicatorPage, SimpleIndicatorGraphPage
from survey.models import HouseholdMemberGroup, Indicator, LocationTypeDetails, EnumerationArea
from survey.models.households import HouseholdHead, Household
from survey.models.backend import Backend
from survey.models.interviewer import Interviewer
from survey.models.formula import *
from survey.models.questions import Question, QuestionOption


def create_household_head(uid, investigator, household_listing, survey_householdlisting):
    household = Household.objects.create(house_number=uid,listing=household_listing,physical_address='Test address' + str(randint(1, 9999)),
                                             last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
    return HouseholdHead.objects.create(surname="sur"+ str(randint(1, 9999)), first_name='fir'+ str(randint(1, 9999)), gender='MALE', date_of_birth="1988-01-01",
                                                          household=household,survey_listing=survey_householdlisting,
                                                          registrar=investigator,registration_channel="ODK Access",
                                                      occupation="Agricultural labor",level_of_education="Primary",
                                                      resident_since='1989-02-02')


@step(u'And I have regions and districts')
def and_i_have_regions_and_districts(step):
    world.country = LocationType.objects.create(name='Country', slug='country')
    world.region = LocationType.objects.create(name='Region', slug='region')
    world.district = LocationType.objects.create(name='District', slug='district')
    world.village = LocationType.objects.create(name='Village', slug='village')

    world.uganda = Location.objects.create(name="Uganda", type=world.country)

    LocationTypeDetails.objects.create(location_type=world.country, country=world.uganda)
    LocationTypeDetails.objects.create(location_type=world.region, country=world.uganda)
    LocationTypeDetails.objects.create(location_type=world.district, country=world.uganda)
    LocationTypeDetails.objects.create(location_type=world.village, country=world.uganda)

    world.west = Location.objects.create(name="WEST", type=world.region, tree_parent=world.uganda)
    world.central = Location.objects.create(name="CENTRAL", type=world.region, tree_parent=world.uganda)
    world.kampala = Location.objects.create(name="Kampala", tree_parent=world.central, type=world.district)
    world.mbarara = Location.objects.create(name="Mbarara", tree_parent=world.west, type=world.district)

    world.kibungo = Location.objects.create(name="Kibungo", type=world.district, tree_parent=world.west)
    world.mpigi = Location.objects.create(name="Mpigi", type=world.district, tree_parent=world.central)

    world.ea = EnumerationArea.objects.get_or_create(name="EA")[0]
    world.ea.locations.add(world.kampala)

    world.ea_mbarara = EnumerationArea.objects.get_or_create(name="EA2")[0]
    world.ea_mbarara.locations.add(world.mbarara)

@step(u'And I have an indicator in that survey')
def and_i_have_an_indicator_in_that_survey(step):
    world.indicator = Indicator.objects.create(name="ITN 1.23", description="rajni indicator",
                                               measure='Percentage',
                                               batch=world.batch_1, module=world.health_module_1)

    world.formula = Formula.objects.create(count=world.question_3, indicator=world.indicator)

@step(u'And I have a multichoice  question')
def and_i_have_a_multichoice_question(step):
    world.member_group = HouseholdMemberGroup.objects.create(name="GENERAL", order=1)
    world.question_3 = Question.objects.create(text="This is a question", module=world.health_module_1,
                                               answer_type=Question.MULTICHOICE, order=3, group=world.member_group)

    world.yes_option = QuestionOption.objects.create(question=world.question_3, text="Yes", order=1)
    world.no_option = QuestionOption.objects.create(question=world.question_3, text="No", order=2)
    world.question_3.batches.add(world.batch_1)
    BatchQuestionOrder.objects.create(question=world.question_3, batch=world.batch_1, order=1)


@step(u'And I have households in in those districts')
def and_i_have_households_in_in_those_districts(step):
    world.household_head_1 = create_household_head(0, world.investigator)
    world.household_head_2 = create_household_head(1, world.investigator)
    world.household_head_3 = create_household_head(2, world.investigator)
    world.household_head_4 = create_household_head(3, world.investigator)
    world.household_head_5 = create_household_head(4, world.investigator)

    world.household_head_6 = create_household_head(5, world.investigator_2)
    world.household_head_7 = create_household_head(6, world.investigator_2)
    world.household_head_8 = create_household_head(7, world.investigator_2)
    world.household_head_9 = create_household_head(8, world.investigator_2)


@step(u'And I have investigators in those districts')
def and_i_have_investigators_in_those_districts(step):
    backend = Backend.objects.create(name="Backend")
    world.investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", ea=world.ea,
                                                     backend=backend)
    world.investigator_2 = Investigator.objects.create(name="Investigator 1", mobile_number="33331",
                                                       ea=world.ea_mbarara,
                                                       backend=backend)


@step(u'And I have responses for that question')
def and_i_have_responses_for_that_question(step):
    world.investigator.member_answered(world.question_3, world.household_head_1, world.yes_option.order, world.batch_1)
    world.investigator.member_answered(world.question_3, world.household_head_2, world.yes_option.order, world.batch_1)
    world.investigator.member_answered(world.question_3, world.household_head_3, world.yes_option.order, world.batch_1)
    world.investigator.member_answered(world.question_3, world.household_head_4, world.no_option.order, world.batch_1)
    world.investigator.member_answered(world.question_3, world.household_head_5, world.no_option.order, world.batch_1)

    world.investigator_2.member_answered(world.question_3, world.household_head_6, world.yes_option.order, world.batch_1)
    world.investigator_2.member_answered(world.question_3, world.household_head_7, world.yes_option.order, world.batch_1)
    world.investigator_2.member_answered(world.question_3, world.household_head_8, world.no_option.order, world.batch_1)
    world.investigator_2.member_answered(world.question_3, world.household_head_9, world.no_option.order, world.batch_1)


@step(u'Given I am on the indicator listing page')
def given_i_am_on_the_indicator_listing_page(step):
    world.page = ListIndicatorPage(world.browser)
    world.page.visit()


@step(u'And I click the analysis link of the indicator')
def and_i_click_the_analysis_link_of_the_indicator(step):
    world.page.click_by_css("#analyse-indicator_%s" % world.indicator.id)


@step(u'Then I should see indicator result page')
def then_i_should_see_indicator_result_page(step):
    world.page = SimpleIndicatorGraphPage(world.browser, world.indicator)
    world.page.validate_url()


@step(u'And I should see indicator graph for the country')
def and_i_should_see_indicator_graph_for_the_country(step):
    world.page.validate_fields_present(['Yes', 'No', '%s Count per %s' % (world.indicator.name, world.region.name)])


@step(u'And I should see indicator data table for the country')
def and_i_should_see_indicator_data_table_for_the_country(step):
    world.page.validate_fields_present(
        [world.region.name, world.district.name, world.yes_option.text, world.no_option.text, 'Total'])

    central_tabulated_data_results = ['3', '2', '5']
    west_tabulated_data_results = ['2', '2', '4']
    world.page.validate_fields_present(central_tabulated_data_results)
    world.page.validate_fields_present(west_tabulated_data_results)


@step(u'And I have an indicator with out a formula')
def and_i_have_an_indicator_with_out_a_formula(step):
    world.indicator_with_no_formula = Indicator.objects.create(name="ITN 1.23", description="rajni indicator",
                                                               measure='Percentage',
                                                               batch=world.batch_1, module=world.health_module_1)

@step(u'Then I should see indicator has no formula message')
def then_i_should_see_indicator_has_no_formula_message(step):
    world.page.see_message("No formula was found in this indicator")

@step(u'And I click that indicators analysis link')
def and_i_click_that_indicators_analysis_link(step):
    world.page.click_by_css("#analyse-indicator_%s" % world.indicator_with_no_formula.id)