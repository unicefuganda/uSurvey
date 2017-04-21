import csv
from time import sleep
import datetime
from lettuce import step, world
from rapidsms.contrib.locations.models import Location, LocationType
from survey.features.page_objects.uploads import UploadWeightsPage
from survey.features.page_objects.weights import ListLocationWeightsPage, ListLocationWeightsErrorLogPage
from survey.models import LocationWeight, UploadErrorLog, Survey, LocationTypeDetails


@step(u'And I have some locations to add weights')
def and_i_have_a_locations(step):
    country = LocationType.objects.create(name='Country', slug='country')
    uganda = Location.objects.create(name="Uganda", type=country)
    LocationTypeDetails.objects.create(country=uganda, location_type=country)

    region_type = LocationType.objects.create(name="region1", slug="region1")
    district_type = LocationType.objects.create(
        name="district1", slug='district1')
    county_type = LocationType.objects.create(name="county1", slug='county1')

    region = Location.objects.create(
        name="region1", type=region_type, tree_parent=uganda)
    district = Location.objects.create(
        name="district1", tree_parent=region, type=district_type)
    Location.objects.create(
        name="county1", tree_parent=district, type=county_type)

    region = Location.objects.create(
        name="region2", tree_parent=uganda, type=region_type)
    district = Location.objects.create(
        name="district2", tree_parent=region, type=district_type)
    Location.objects.create(
        name="county2", tree_parent=district, type=county_type)


@step(u'When I visit upload locations weights page')
def when_i_visit_upload_locations_weights_page(step):
    world.page = UploadWeightsPage(world.browser)
    world.page.visit()


@step(u'Then I should see upload weights form fields')
def then_i_should_see_upload_weights_form_fields(step):
    world.page.validate_fields_present(
        ["Upload Location Weights", "Survey", "Location weights file"])


@step(u'Then I should see table of location weights layout')
def then_i_should_see_table_of_location_weights_layout(step):
    world.type_names = [type.name.capitalize(
    ) + 'Name' for type in LocationType.objects.all()]
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
    country = LocationType.objects.create(name="Country", slug="country")
    uganda = Location.objects.create(name="Uganda", type=country)
    LocationTypeDetails.objects.create(country=uganda, location_type=country)

    reqion_type = LocationType.objects.create(name="region1", slug="region1")
    district_type = LocationType.objects.create(
        name="district1", slug='district1')
    county_type = LocationType.objects.create(name="county1", slug='county1')

    region = Location.objects.create(
        name="region1", type=reqion_type, tree_parent=uganda)
    district = Location.objects.create(
        name="district1", tree_parent=region, type=district_type)
    county = Location.objects.create(
        name="county1", tree_parent=district, type=county_type)

    region = Location.objects.create(
        name="region2", type=reqion_type, tree_parent=uganda)
    district = Location.objects.create(
        name="district2", tree_parent=region, type=district_type)
    county1 = Location.objects.create(
        name="county2", tree_parent=district, type=county_type)
    world.weight_1 = LocationWeight.objects.create(
        location=county, selection_probability=0.1, survey=world.survey)
    world.weight_2 = LocationWeight.objects.create(
        location=county1, selection_probability=0.2, survey=world.survey)


@step(u'And I have error logs from location weights upload')
def and_i_have_error_logs_from_location_weights_upload(step):
    world.error_log = UploadErrorLog.objects.create(
        model="WEIGHTS", filename="some_file.csv", error="Some error")
    world.error_log2 = UploadErrorLog.objects.create(
        model="WEIGHTS", filename="some_file.csv", error="Some error two")


@step(u'And I visit the list location weights page')
def and_i_visit_the_list_location_weights_page(step):
    world.page = ListLocationWeightsPage(world.browser)
    world.page.visit()


@step(u'Then I should see the locations weights')
def then_i_should_see_the_locations_weights(step):
    weight_1_details = [
        world.weight_1.location.name, str(
            world.weight_1.selection_probability), str(
            world.weight_1.survey.get_total_respondents()), str(
                world.weight_1.survey.sample_size)]
    weight_2_details = [
        world.weight_2.location.name, str(
            world.weight_2.selection_probability), str(
            world.weight_2.survey.get_total_respondents()), str(
                world.weight_1.survey.sample_size)]
    world.page.validate_fields_present(weight_1_details)
    world.page.validate_fields_present(weight_2_details)


@step(u'When i click the view error logs link')
def when_i_click_the_view_error_logs_link(step):
    world.page.click_by_css("#view_error_log")


@step(u'Then I should see the error logs from previous the month')
def then_i_should_see_the_error_logs_from_previous_the_month(step):
    world.page = ListLocationWeightsErrorLogPage(world.browser)
    world.page.validate_fields_present(
        [world.error_log.filename, world.error_log.error])
    world.page.validate_fields_present(
        [world.error_log2.filename, world.error_log2.error])


@step(u'And I have two surveys')
def and_i_have_two_surveys(step):
    world.survey_1 = Survey.objects.create(name="Survey 1")
    world.survey_2 = Survey.objects.create(name="Survey 2")


@step(u'And I select one survey')
def and_i_select_one_survey(step):
    world.page.select("survey", [world.survey_2.id])


@step(u'And I have a number of locations and weights in each survey')
def and_i_have_a_number_of_locations_and_weights_in_each_survey(step):
    country = LocationType.objects.create(name='Country', slug='country')
    uganda = Location.objects.create(name="Uganda", type=country)
    LocationTypeDetails.objects.create(country=uganda, location_type=country)

    county = LocationType.objects.create(name="County", slug="county")
    world.county1 = Location.objects.create(
        name="county1", type=county, tree_parent=uganda)
    world.county2 = Location.objects.create(
        name="county2", type=county, tree_parent=uganda)
    world.weight_1 = LocationWeight.objects.create(
        location=world.county1,
        selection_probability=0.1,
        survey=world.survey_1)
    world.weight_2 = LocationWeight.objects.create(
        location=world.county2,
        selection_probability=0.2,
        survey=world.survey_2)
    world.weight_3 = LocationWeight.objects.create(
        location=world.county1,
        selection_probability=0.22,
        survey=world.survey_2)


@step(u'And I click get list')
def and_i_click_get_list(step):

    world.page.click_by_css("#get_list")


@step(u'Then I should see the location weights in that survey')
def then_i_should_see_the_location_weights_in_that_survey(step):
    weight_3_details = [
        world.weight_3.location.name, str(
            world.weight_3.selection_probability), str(
            world.weight_3.survey.get_total_respondents()), str(
                world.weight_3.survey.sample_size)]
    weight_2_details = [
        world.weight_2.location.name, str(
            world.weight_2.selection_probability), str(
            world.weight_2.survey.get_total_respondents()), str(
                world.weight_1.survey.sample_size)]
    world.page.validate_fields_present(weight_3_details)
    world.page.validate_fields_present(weight_2_details)


@step(u'When I select a location')
def when_i_select_a_location(step):
    world.page.fill_in_with_js('$("#location-county")', world.county1.id)


@step(u'Then I should see the weights for that location and survey')
def then_i_should_see_the_weights_for_that_location_and_survey(step):
    weight_3_details = [
        world.weight_3.location.name, str(
            world.weight_3.selection_probability), str(
            world.weight_3.survey.get_total_respondents()), str(
                world.weight_3.survey.sample_size)]
    world.page.validate_fields_present(weight_3_details)


@step(u'When I click the upload weights link')
def when_i_click_the_upload_weights_link(step):
    world.page.click_by_css('#upload_weights')


@step(u'Then I should see upload weights page')
def then_i_should_see_upload_weights_page(step):
    world.page = UploadWeightsPage(world.browser)
    world.page.validate_url()


@step(u'And I have some 100 locations with weights')
def and_i_have_some_100_locations_with_weights(step):
    country = LocationType.objects.create(name="Country", slug="country")
    uganda = Location.objects.create(name="Uganda", type=country)
    LocationTypeDetails.objects.create(country=uganda, location_type=country)

    reqion_type = LocationType.objects.create(name="region1", slug="region1")
    district_type = LocationType.objects.create(
        name="district1", slug='district1')
    county_type = LocationType.objects.create(name="county1", slug='county1')

    region = Location.objects.create(
        name="region1", type=reqion_type, tree_parent=uganda)
    district = Location.objects.create(
        name="district1", tree_parent=region, type=district_type)
    county = Location.objects.create(
        name="county1", tree_parent=district, type=county_type)

    for i in xrange(100):
        location = Location.objects.create(
            name=str(i), tree_parent=district, type=county_type)
        LocationWeight.objects.create(
            location=location,
            selection_probability=i / 100.0,
            survey=world.survey)


@step(u'Then I see locations weights paginated')
def then_i_see_locations_weights_paginated(step):
    world.page.validate_pagination()


@step(u'And I have some error logs for upload weights')
def and_i_have_some_error_logs_for_upload_weights(step):
    world.error_log = UploadErrorLog.objects.create(
        model="WEIGHTS", filename="some_file.csv", error="Some error")
    world.error_log2 = UploadErrorLog.objects.create(
        model="WEIGHTS", filename="some_file_1.csv", error="Some error two")
    world.error_log3 = UploadErrorLog.objects.create(
        model="LOCATION", filename="some_file_2.csv", error="Some error three")

    world.timedelta = datetime.timedelta(days=4)
    world.error_log2.created += world.timedelta
    world.error_log2.save()


@step(u'And I visit the weights error logs page')
def and_i_visit_the_weights_error_logs_page(step):
    world.page = ListLocationWeightsErrorLogPage(world.browser)
    world.page.visit()


@step(u'Then I should see all error logs')
def then_i_should_see_all_error_logs(step):
    world.page.validate_fields_present(
        [world.error_log.filename, world.error_log.error])
    world.page.validate_fields_present(
        [world.error_log2.filename, world.error_log2.error])
    world.page.validate_fields_present(
        [world.error_log3.filename, world.error_log3.error], False)


@step(u'When I select from and to dates')
def when_i_select_from_and_to_dates(step):
    dates = {'from_date': world.error_log.created.strftime('%Y-%m-%d'),
             'to_date': world.error_log.created.strftime('%Y-%m-%d')}
    world.page.fill_valid_values(dates)


@step(u'Then I should see only error logs between those dates')
def then_i_should_see_only_error_logs_between_those_dates(step):
    world.page.validate_fields_present(
        [world.error_log.filename, world.error_log.error])
    world.page.validate_fields_present(
        [world.error_log2.filename, world.error_log2.error], False)


@step(u'And I click the filter link')
def and_i_click_the_filter_link(step):
    world.page.click_by_css('#get_logs')
