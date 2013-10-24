from rapidsms.contrib.locations.models import Location
from survey.models.locations import LocationCode
from survey.tests.base_test import BaseTest

class LocationCodeTest(BaseTest):
    def test_fields(self):
        location_code = LocationCode()
        fields = [str(item.attname) for item in location_code._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'location_id', 'code']:
            self.assertIn(field, fields)

    def test_store(self):
        uganda = Location.objects.create(name='Uganda')
        location_code = LocationCode.objects.create(location=uganda, code=0)
        self.failUnless(location_code.id)

