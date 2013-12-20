import csv
from time import sleep
from lettuce import step, world
from rapidsms.contrib.locations.models import Location, LocationType
from survey.features.page_objects.uploads import UploadEAPage
from survey.models import LocationTypeDetails


@step(u'And I have some locations to add EA')
def and_i_have_some_locations_to_add_ea(step):
    country = LocationType.objects.create(name='Country', slug='country')
    uganda = Location.objects.create(name="Uganda", type=country)
    LocationTypeDetails.objects.create(country=uganda, location_type=country)

    region_type = LocationType.objects.create(name="regiontype", slug="regiontype")
    district_type = LocationType.objects.create(name="districttype", slug='districttype')
    county_type = LocationType.objects.create(name="countytype", slug='countytype')
    parish_type = LocationType.objects.create(name="parishtype", slug='parishtype')

    region = Location.objects.create(name="region1", type=region_type, tree_parent=uganda)
    district = Location.objects.create(name="district1", tree_parent=region, type=district_type)
    county_1 = Location.objects.create(name="county1", tree_parent=district, type=county_type)
    parish_1 = Location.objects.create(name="parish_1", tree_parent=county_1, type=parish_type)
    parish_1_b = Location.objects.create(name="parish_1b", tree_parent=county_1, type=parish_type)

    region = Location.objects.create(name="region2", tree_parent=uganda, type=region_type)
    district = Location.objects.create(name="district2", tree_parent=region, type=district_type)
    county_2 = Location.objects.create(name="county2", tree_parent=district, type=county_type)
    parish_2 = Location.objects.create(name="parish_2", tree_parent=county_2, type=parish_type)


@step(u'When I visit upload EA page')
def when_i_visit_upload_ea_page(step):
    world.page = UploadEAPage(world.browser)
    world.page.visit()


@step(u'Then I should see EA upload form fields')
def then_i_should_see_ea_upload_form_fields(step):
    world.page.validate_fields_present(["Upload Enumeration Areas", "Survey", "EA file"])


@step(u'Then I should see table of EA layout')
def then_i_should_see_table_of_ea_layout(step):
    world.type_names = [type.name for type in LocationType.objects.exclude(name__iexact="country")]
    world.page.validate_fields_present(world.type_names)


@step(u'When I have a EA csv file')
def when_i_have_a_ea_csv_file(step):
    filedata =  [
                ['Regiontype', 'Districttype', 'Counttype', 'EA',                   'Parishtype', 'EA'],
                ['region1',    'district1',    'county1',   'ea_containing_parish', 'parish_1',   ''],
                ['region1',    'district1',    'county1',   'ea_containing_parish', 'parish_1b',  ''],
                ['region2',    'district2',    'county2',   '',                     'parish2',    'ea_under_parish'],
                ['region2',    'district2',    'county2',   '',                     'parish2',    'ea_under_parish']]

    write_to_csv('wb', filedata, 'test.csv')


def write_to_csv(mode, data, csvfilename):
    with open(csvfilename, mode) as fp:
        file = csv.writer(fp, delimiter=',')
        file.writerows(data)


@step(u'Then I should see EA upload is in progress')
def then_i_should_see_ea_upload_is_in_progress(step):
    world.page.is_text_present('Upload in progress. This could take a while.')


@step(u'Then said EA layout should collapse')
def then_said_ea_layout_should_collapse(step):
    sleep(3)
    world.page.validate_layout_collapsed()