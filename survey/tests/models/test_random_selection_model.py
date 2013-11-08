# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import random
from django.test import TestCase
from mock import patch
import mock
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import RandomHouseHoldSelection, Investigator, Backend, Household, Survey


class RandomHouseHoldSelectionTest(TestCase):
    def test_store(self):
        selection = RandomHouseHoldSelection.objects.create(mobile_number="123456789", no_of_households=50,
                                                            selected_households="1,2,3,4,5,6,7,8,9,10")
        self.failUnless(selection.id)

    def test_creates_households_for_an_investigator_when_saving_random_sample(self):
        backend = Backend.objects.create(name="Backend")
        location_type = LocationType.objects.create(name="District", slug="district")
        mobile_number = "123456789"
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        investigator = Investigator.objects.create(mobile_number=mobile_number,
                                                   location=Location.objects.create(name="Kampala", type=location_type),
                                                   backend=backend)

        random_households = [1, 3, 4, 7, 9, 13, 20, 28, 39, 70]

        with patch.object(random, 'sample', return_value=random_households):
            random_selection_object = RandomHouseHoldSelection(mobile_number=mobile_number, survey=open_survey)
            random_selection_object.send_message = mock.MagicMock()
            random_selection_object.generate(100, open_survey)

        self.assertEqual(len(random_households), len(investigator.households.all()))
        for random_household in random_households:
            self.assertIn(Household.objects.get(random_sample_number=random_household), investigator.households.all())