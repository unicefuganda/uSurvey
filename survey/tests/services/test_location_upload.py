import os
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models.locations import *
from survey.models import LocationTypeDetails, UploadErrorLog
from survey.services.location_upload import UploadLocation
from survey.tests.base_test import BaseTest


class LocationUploadHelper(BaseTest):
    def setUp(self):
        self.data = [['RegionName', 'DistrictName', 'CountyName'],
                     ['region1', 'district1', 'county1'],
                     ['region2', 'district2', 'county2']]

        self.write_to_csv('wb', self.data)
        self.filename = 'test.csv'
        file = open(self.filename, 'rb')
        self.uploader = UploadLocation(file)
        self.region = LocationType.objects.create(name='Region', slug='region')
        self.district = LocationType.objects.create(name='District', slug='district', parent=self.region)
        self.county = LocationType.objects.create(name='County', slug='county', parent=self.district)
        LocationTypeDetails.objects.create(location_type=self.region, required=True, has_code=False)
        LocationTypeDetails.objects.create(location_type=self.district, required=True, has_code=False)
        LocationTypeDetails.objects.create(location_type=self.county, required=True, has_code=False)

    def tearDown(self):
        os.system("rm -rf %s"%self.filename)

