import csv
from time import sleep
from lettuce import step, world
from rapidsms.contrib.locations.models import Location, LocationType
from survey.features.page_objects.uploads import UploadWeightsPage


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
    world.type_names = [ type.name.capitalize() + 'Name' for type in LocationType.objects.all()]
    world.page.validate_fields_present(world.type_names)

@step(u'And I select a survey')
def and_i_select_a_survey(step):
    world.page.select('survey', [world.survey.id])

@step(u'When I have a locations weights csv file')
def when_i_have_a_locations_weights_csv_file(step):
    filedata = [world.type_names,
                ['region1',  'district1', 'county1', '0.02'],
                ['region2', 'district2', 'county2', '0.1']]
    write_to_csv('wb', filedata, 'test.csv')

def write_to_csv(mode, data, csvfilename):
    with open(csvfilename, mode) as fp:
        file = csv.writer(fp, delimiter=',')
        file.writerows(data)

@step(u'Then I should see location weights successfully added')
def then_i_should_see_location_weights_successfully_added(step):
    world.page.see_success_message('Location weights', 'uploaded')

@step(u'Then said weight layout should collapse')
def then_said_weight_layout_should_collapse(step):
    sleep(3)
    world.page.validate_layout_collapsed()