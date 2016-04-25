import os
from survey.models.locations import *
from survey.models import Survey, UploadErrorLog, EnumerationArea, LocationTypeDetails
from survey.services.ea_upload import UploadEA, UploadEACSVLayoutHelper
from survey.tests.base_test import BaseTest
from django.utils.timezone import utc


class EAUploadTest(BaseTest):
    def setUp(self):
        self.data = [
                ['Regiontype', 'Districttype', 'Counttype', 'EA',                   'Parishtype', 'EA'],
                ['region1',    'district1',    'county1',   'ea_containing_parish', 'parish_1',   ''],
                ['region1',    'district1',    'county1',   'ea_containing_parish', 'parish_1b',  ''],
                ['region2',    'district2',    'county2',   '',                     'parish2',    'ea_under_parish'],
                ['region2',    'district2',    'county2',   '',                     'parish2',    'ea_under_parish']]

        self.write_to_csv('wb', self.data)
        self.filename = 'test.csv'
        _file = open(self.filename, 'rb')
        self.uploader = UploadEA(_file)
        self.survey = Survey.objects.create(name="Survey A")

    def tearDown(self):
        os.system("rm -rf %s" % self.filename)

    def test_should_return_false__and_message_if_location_not_found(self):
        Location.objects.all().delete()
        self.uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(4, error_log.count())
        self.failUnless(error_log.filter(row_number=1,
                                         error='There is no parishtype with name: parish_1, in county1.'))
        self.failUnless(error_log.filter(row_number=2,
                                         error='There is no parishtype with name: parish_1b, in county1.'))
        self.failUnless(error_log.filter(row_number=3,
                                         error='There is no parishtype with name: parish2, in county2.'))
        self.failUnless(error_log.filter(row_number=4,
                                         error='There is no parishtype with name: parish2, in county2.'))

    def test_should_return_false__and_message_if_location_is_blank(self):
        EMPTY_PARISH_NAME = ''
        data = [
                ['Regiontype', 'Districttype', 'Counttype', 'EA',                   'Parishtype', 'EA'],
                ['region1',    'district1',    'county1',   'ea_containing_parish', EMPTY_PARISH_NAME,   '']]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        rtype=LocationType.objects.create(name="Region",slug="region")
        region = Location.objects.create(name="region1",type=rtype)
        dtype=LocationType.objects.create(name="District",slug="district",parent=rtype)
        district = Location.objects.create(name="district1", parent=region,type=dtype)
        ctype=LocationType.objects.create(name="County",slug="county",parent=dtype)
        Location.objects.create(name="county1", parent=district,type=ctype)

        uploader = UploadEA(_file)
        uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(1, error_log.count())
        self.assertEqual(1, error_log[0].row_number)
        self.assertEqual('There is no parishtype with name: , in county1.', error_log[0].error)

    def test_should_return_false__and_message_if_location_tree_parent_does_not_match_one_provided(self):
        rtype1=LocationType.objects.create(name="Region1",slug="region")
        region = Location.objects.create(name="region name not matching the one in first row of file", type=rtype1)
        dtype1=LocationType.objects.create(name="District",slug="district",parent=rtype1)
        district = Location.objects.create(name="district1",parent=region,type=dtype1)
        ctype1=LocationType.objects.create(name="County",slug="county",parent=dtype1)
        county = Location.objects.create(name="county1", parent=district,type=ctype1)
        ptype1=LocationType.objects.create(name="Parish",slug="parish",parent=ctype1)
        l = Location.objects.create(name="parish_1", parent=county,type=ptype1)
        self.uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(4, error_log.count())
        self.assertEqual('The location hierarchy region1 >> district1 >> county1 >> parish_1 does not exist.', error_log.get(row_number=1).error)

    def test_should_return_false__and_message_if_no_EA_is_provided(self):
        EMPTY_EA_NAME = ''
        data = [
                ['Regiontype', 'Districttype', 'Counttype', 'EA', 'Parishtype', 'EA'],
                ['region1',    'district1',    'county1',   '',   'parish_1',   EMPTY_EA_NAME]]
        self.write_to_csv('wb', data)
        _file = open(self.filename, 'rb')

        rtype1=LocationType.objects.create(name="Region1",slug="region")
        region = Location.objects.create(name="r1", type=rtype1)
        dtype1=LocationType.objects.create(name="District",slug="district",parent=rtype1)
        district = Location.objects.create(name="district1",parent=region,type=dtype1)
        ctype1=LocationType.objects.create(name="County",slug="county",parent=dtype1)
        county = Location.objects.create(name="county1", parent=district,type=ctype1)
        ptype1=LocationType.objects.create(name="Parish",slug="parish",parent=ctype1)
        l = Location.objects.create(name="parish_1", parent=county,type=ptype1)
        uploader = UploadEA(_file)

        uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.assertEqual(1, error_log.count())
        self.assertEqual(1, error_log[0].row_number)

    def test_not_csv_file(self):
        EnumerationArea.objects.all().delete()
        self.filename = 'not_csv.xls'
        self.generate_non_csv_file(self.filename)
        file = open(self.filename,'rb')
        uploader = UploadEA(file)

        uploader.upload(self.survey)
        error_log = UploadErrorLog.objects.filter(model=self.uploader.MODEL, filename=self.filename)
        self.failUnless(error_log.filter(error='Enumeration Areas not uploaded. %s is not a valid csv file.' % self.filename))
        self.failIf(EnumerationArea.objects.all())


class EAUploadCSVLayoutHelperTest(BaseTest):
    def setUp(self):
        self.country = LocationType.objects.create(name='Country', slug='country')
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.country)

        self.region_type = LocationType.objects.create(name="Regiontype", slug="regiontype",parent=self.country)
        self.district_type = LocationType.objects.create(name="Districttype", slug='districttype',parent=self.region_type)
        self.county_type = LocationType.objects.create(name="Countytype", slug='countytype',parent=self.district_type)
        self.parish_type = LocationType.objects.create(name="Parishtype", slug='parishtype',parent=self.county_type)

        self.region = Location.objects.create(name="region1", type=self.region_type, parent=self.uganda)
        self.district = Location.objects.create(name="district1", parent=self.region, type=self.district_type)
        self.county_1 = Location.objects.create(name="county1", parent=self.district, type=self.county_type)
        self.parish_1 = Location.objects.create(name="parish_1", parent=self.county_1, type=self.parish_type)
        self.parish_1_b = Location.objects.create(name="parish_1b", parent=self.county_1, type=self.parish_type)

        self.region = Location.objects.create(name="region2", parent=self.uganda, type=self.region_type)
        self.district = Location.objects.create(name="district2", parent=self.region, type=self.district_type)
        self.county_2 = Location.objects.create(name="county2", parent=self.district, type=self.county_type)
        self.parish_2 = Location.objects.create(name="parish_2", parent=self.county_2, type=self.parish_type)

        self.ea_csv_layout = UploadEACSVLayoutHelper()

    def test_headers_format(self):
        expected_headers = ['Regiontype', 'Districttype', 'Countytype', 'EA', 'Parishtype', 'EA']
        [self.assertIn(header, expected_headers) for header in self.ea_csv_layout._header_format()]

    def test_table_layout_example(self):
       expected = [
                ['regiontype_0',    'districttype_0',    'countytype_0',   'ea_0', 'parishtype_0',   ''],
                ['regiontype_0',    'districttype_0',    'countytype_0',   'ea_0', 'parishtype_0_b',   ''],
                ['regiontype_1',    'districttype_1',    'countytype_1',   '', 'parishtype_1',   'ea_1'],
                ['regiontype_1',    'districttype_1',    'countytype_1',   '', 'parishtype_1',   'ea_1_b']]
       self.assertEqual(expected, self.ea_csv_layout.table_layout_example())

    def test_table_layout_when_no_location_type_or_location_yet(self):
        LocationType.objects.all().delete()
        LocationTypeDetails.objects.all().delete()
        Location.objects.all().delete()
        ea_csv_layout = UploadEACSVLayoutHelper()
        self.assertEqual([["No Location/LocationType added yet. Please add those first."]], ea_csv_layout.table_layout_example())
