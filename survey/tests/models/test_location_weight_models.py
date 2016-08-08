from survey.models import Survey
from survey.models.location_weight import LocationWeight
from survey.models.locations import LocationType, Location
from survey.tests.base_test import BaseTest


class LocationTypeDetailsTest(BaseTest):
    def test_fields(self):
        location_weight = LocationWeight()
        fields = [str(item.attname) for item in location_weight._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created', 'modified', 'location_id', 'survey_id', 'selection_probability']:
            self.assertIn(field, fields)

    def test_store(self):

        country = LocationType.objects.create(name='country', slug='country')
        uganda = Location.objects.create(name="Uganda", type=country)
        district = LocationType.objects.create(name='district', slug='district')
        location = Location.objects.create(name="Kampala", type=district, parent=uganda)

        survey = Survey.objects.create(name="Kampala Survey")
        location_weight = LocationWeight.objects.create(location=location, survey=survey, selection_probability=0.2)
        self.failUnless(location_weight.id)
        self.assertEqual(location_weight.selection_probability, 0.2)
        self.assertEqual(location_weight.survey, survey)