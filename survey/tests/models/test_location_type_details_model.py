from rapidsms.contrib.locations.models import LocationType
from survey.models.location_type_details import LocationTypeDetails
from survey.tests.base_test import BaseTest


class LocationTypeDetailsTest(BaseTest):

    def test_fields(self):
        location_type_details = LocationTypeDetails()
        fields = [str(item.attname) for item in location_type_details._meta.fields]
        self.assertEqual(7, len(fields))
        for field in ['id', 'created', 'modified', 'location_type_id', 'required', 'has_code', 'code']:
            self.assertIn(field, fields)

    def test_store(self):
        country = LocationType.objects.create(name='country',slug='country')
        location_type_details = LocationTypeDetails.objects.create(required=True,has_code=False,location_type=country)
        self.failUnless(location_type_details.id)
