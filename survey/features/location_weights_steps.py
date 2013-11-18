import csv
from time import sleep
from lettuce import step, world
from rapidsms.contrib.locations.models import Location, LocationType
from survey.features.page_objects.uploads import UploadWeightsPage, ListLocationWeightsPage, ListLocationWeightsErrorLogPage
from survey.models import LocationWeight, UploadErrorLog, Survey


@step(u'And I have some locations to add weights')
def and_i_have_a_locations(step):
    LocationType.objects.create(name="region1", slug="region1")
    LocationType.objects.create(name="district1", slug='district1')
    LocationType.objects.create(name="county1", slug='county1')

    region = Location.objects.create(name="region1")
    district = Location.objects.create(name="district1", tree_parent=region)
    Location.objects.create(name="county1", tree_parent=district)

    region = Location.objects.create(name="region2")
    district = Location.objects.create(name="district2", tree_parent=region)
    Location.objects.create(name="county2", tree_parent=district)


@step(u'When I visit upload locations weights page')
def when_i_visit_upload_locations_weights_page(step):
    world.page = UploadWeightsPage(world.browser)
    world.page.visit()


@step(u'Then I should see upload weights form fields')
def then_i_should_see_upload_weights_form_fields(step):
    world.page.validate_fields_present(["Upload Location Weights", "Survey", "Location weights file"])


@step(u'Then I should see table of location weights layout')
def then_i_should_see_table_of_location_weights_layout(step):
    world.type_names = [type.name.capitalize() + 'Name' for type in LocationType.objects.all()]
    world.page.validate_fields_present(world.type_names)


@step(u'And I select a survey')
def and_i_select_a_survey(step):
    world.page.select('survey', [world.survey.id])


@step(u'When I have a locations weights csv file')
def when_i_have_a_locations_weights_csv_file(step):
    filedata = [world.type_names,
                ['region1', 'district1', 'county1', '0.02'],
                ['region2', 'district2', 'county2', '0.1']]
    write_to_csv('wb', filedata, 'test.csv')


def write_to_csv(mode, data, csvfilename):
    with open(csvfilename, mode) as fp:
        file = csv.writer(fp, delimiter=',')
        file.writerows(data)


@step(u'Then I should see location weights upload is in progress')
def then_i_should_see_location_weights_successfully_added(step):
    world.page.is_text_present('Upload in progress. This could take a while.')


@step(u'Then said weight layout should collapse')
def then_said_weight_layout_should_collapse(step):
    sleep(3)
    world.page.validate_layout_collapsed()


@step(u'And I have some locations with weights')
def and_i_have_some_locations_to_with_weights(step):
    reqion_type = LocationType.objects.create(name="region1", slug="region1")
    district_type = LocationType.objects.create(name="district1", slug='district1')
    county_type = LocationType.objects.create(name="county1", slug='county1')

    region = Location.objects.create(name="region1", type=reqion_type)
    district = Location.objects.create(name="district1", tree_parent=region, type=district_type)
    county = Location.objects.create(name="county1", tree_parent=district, type=county_type)

    region = Location.objects.create(name="region2", type=reqion_type)
    district = Location.objects.create(name="district2", tree_parent=region, type=district_type)
    county1 = Location.objects.create(name="county2", tree_parent=district, type=county_type)
    world.weight_1 = LocationWeight.objects.create(location=county, selection_probability=0.1, survey=world.survey)
    world.weight_2 = LocationWeight.objects.create(location=county1, selection_probability=0.2, survey=world.survey)


@step(u'And I have error logs from location weights upload')
def and_i_have_error_logs_from_location_weights_upload(step):
    world.error_log = UploadErrorLog.objects.create(model="WEIGHTS", filename="some_file.csv", error="Some error")
    world.error_log2 = UploadErrorLog.objects.create(model="WEIGHTS", filename="some_file.csv", error="Some error two")


@step(u'And I visit the list location weights page')
def and_i_visit_the_list_location_weights_page(step):
    world.page = ListLocationWeightsPage(world.browser)
    world.page.visit()


@step(u'Then I should see the locations weights')
def then_i_should_see_the_locations_weights(step):
    weight_1_details = [world.weight_1.location.name, str(world.weight_1.selection_probability),
                        str(world.weight_1.survey.get_total_respondents()), str(world.weight_1.survey.sample_size)]
    weight_2_details = [world.weight_2.location.name, str(world.weight_2.selection_probability),
                        str(world.weight_2.survey.get_total_respondents()), str(world.weight_1.survey.sample_size)]
    world.page.validate_fields_present(weight_1_details)
    world.page.validate_fields_present(weight_2_details)


@step(u'When i click the view error logs link')
def when_i_click_the_view_error_logs_link(step):
    world.page.click_by_css("#view_error_log")


@step(u'Then I should see the error logs from previous the month')
def then_i_should_see_the_error_logs_from_previous_the_month(step):
    world.page = ListLocationWeightsErrorLogPage(world.browser)
    world.page.validate_fields_present([world.error_log.filename, world.error_log.error])
    world.page.validate_fields_present([world.error_log2.filename, world.error_log2.error])

@step(u'And I have two surveys')
def and_i_have_two_surveys(step):
    world.survey_1 = Survey.objects.create(name="Survey 1")
    world.survey_2 = Survey.objects.create(name="Survey 2")


@step(u'And I select one survey')
def and_i_select_one_survey(step):
    world.page.select("survey", [world.survey_2.id])

@step(u'And I have a number of locations and weights in each survey')
def and_i_have_a_number_of_locations_and_weights_in_each_survey(step):
    county = LocationType.objects.create(name="County", slug="county")
    world.county1 = Location.objects.create(name="county1", type=county)
    world.county2 = Location.objects.create(name="county2", type=county)
    world.weight_1 = LocationWeight.objects.create(location=world.county1, selection_probability=0.1, survey=world.survey_1)
    world.weight_2 = LocationWeight.objects.create(location=world.county2, selection_probability=0.2, survey=world.survey_2)
    world.weight_3 = LocationWeight.objects.create(location=world.county1, selection_probability=0.22, survey=world.survey_2)

@step(u'And I click get list')
def and_i_click_get_list(step):

    world.page.click_by_css("#get_list")

@step(u'Then I should see the location weights in that survey')
def then_i_should_see_the_location_weights_in_that_survey(step):
    weight_3_details = [world.weight_3.location.name, str(world.weight_3.selection_probability),
                        str(world.weight_3.survey.get_total_respondents()), str(world.weight_3.survey.sample_size)]
    weight_2_details = [world.weight_2.location.name, str(world.weight_2.selection_probability),
                        str(world.weight_2.survey.get_total_respondents()), str(world.weight_1.survey.sample_size)]
    world.page.validate_fields_present(weight_3_details)
    world.page.validate_fields_present(weight_2_details)

@step(u'When I select a location')
def when_i_select_a_location(step):
    world.page.fill_in_with_js('$("#location-county")', world.county1.id)

@step(u'Then I should see the weights for that location and survey')
def then_i_should_see_the_weights_for_that_location_and_survey(step):
    weight_3_details = [world.weight_3.location.name, str(world.weight_3.selection_probability),
                        str(world.weight_3.survey.get_total_respondents()), str(world.weight_3.survey.sample_size)]
    world.page.validate_fields_present(weight_3_details)

