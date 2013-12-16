from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import Investigator, Backend, EnumerationArea, Survey
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

    def test_investigator_knows_how_to_get_household_code(self):
        country = LocationType.objects.create(name="Country", slug=slugify("country"))
        city = LocationType.objects.create(name="City", slug=slugify("city"))
        subcounty = LocationType.objects.create(name="Subcounty", slug=slugify("subcounty"))
        parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=city, tree_parent=uganda)
        abim = Location.objects.create(name="Abim", type=subcounty, tree_parent=kampala)
        kololo = Location.objects.create(name="Kololo", type=parish, tree_parent=abim)
        village = Location.objects.create(name="Village", type=village, tree_parent=kololo)

        uganda_code_value = '1'
        kampala_code_value = '22'
        abim_code_value = '333'
        kololo_code_value = '4444'
        village_code_value = '55555'

        LocationCode.objects.create(location=uganda, code=uganda_code_value)
        LocationCode.objects.create(location=kampala, code=kampala_code_value)
        LocationCode.objects.create(location=abim, code=abim_code_value)
        LocationCode.objects.create(location=kololo, code=kololo_code_value)
        LocationCode.objects.create(location=village, code=village_code_value)
        backend = Backend.objects.create(name="Backend")
        survey = Survey.objects.create(name="huhu")
        ea = EnumerationArea.objects.create(name="EA2", survey=survey)
        ea.locations.add(village)

        investigator = Investigator.objects.create(name="investigator name", mobile_number="9876543210",
                                                   ea=ea, backend=backend)
        household_code_value = uganda_code_value + kampala_code_value + abim_code_value + kololo_code_value + village_code_value
        self.assertEqual(household_code_value, LocationCode.get_household_code(investigator))