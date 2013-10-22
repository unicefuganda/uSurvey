from unittest import TestCase
from rapidsms.contrib.locations.models import LocationType
from survey.views.location_upload_view_helper import UploadLocation


class LocationUploadHelper(TestCase):
    def setUp(self):
        import csv
        with open('test.csv', 'wb') as fp:
            file = csv.writer(fp, delimiter=',')
            data = [['Region', 'District'],
                    ['region1', 'district1'],
                    ['region2', 'district2']]
            file.writerows(data)
            self.uploader = UploadLocation('test.csv')

    def test_should_return_false__and_message_if_location_type_not_found(self):
        status,message= self.uploader.upload()
        self.assertFalse(status)
        self.assertEqual(message, 'Location type - Region not created')

    def test_should_return_true_if_location_type_exists(self):
        LocationType.objects.create(name='Region',slug='region')
        LocationType.objects.create(name='District',slug='district')
        status,message= self.uploader.upload()
        self.assertTrue(status)
        self.assertEqual(message, 'Successfully uploaded')