from datetime import date
from django.core.exceptions import ValidationError
from django.db import DatabaseError

from rapidsms.contrib.locations.models import Location, LocationType
from survey.models import BatchQuestionOrder, GroupCondition, Survey, LocationTypeDetails

from survey.models.batch import Batch
from survey.models.backend import Backend
from survey.models.enumeration_area import EnumerationArea
from survey.models.households import Household, HouseholdMember
from survey.models.investigator import Investigator
from survey.models.question import Question
from survey.models.householdgroups import HouseholdMemberGroup
from survey.tests.base_test import BaseTest


class EATest(BaseTest):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        self.batch = Batch.objects.create(order=1, survey=self.survey)
        self.country = LocationType.objects.create(name="Country", slug="country")
        self.region = LocationType.objects.create(name="Region", slug="region")
        self.district = LocationType.objects.create(name="District", slug='district')

        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        LocationTypeDetails.objects.create(location_type=self.country, country=self.uganda)
        self.west = Location.objects.create(name="WEST", type=self.region, tree_parent=self.uganda)
        self.central = Location.objects.create(name="CENTRAL", type=self.region, tree_parent=self.uganda)
        self.kampala = Location.objects.create(name="Kampala", tree_parent=self.central, type=self.district)
        self.wakiso = Location.objects.create(name="Wakiso", tree_parent=self.central, type=self.district)
        self.mbarara = Location.objects.create(name="Mbarara", tree_parent=self.west, type=self.district)

    def test_ea_fields(self):
        ea = EnumerationArea()

        fields = [str(item.attname) for item in ea._meta.fields]

        for field in ['id', 'name', 'survey_id', 'created', 'modified']:
            self.assertIn(field, fields)
        self.assertEqual(len(fields), 5)

    def test_store(self):
        ea = EnumerationArea.objects.create(name="EA1", survey=self.survey)
        self.failUnless(ea.id)

    def test_add_location(self):
        ea = EnumerationArea.objects.create(name="EA1", survey=self.survey)
        ea.locations.add(self.kampala)
        self.failUnless(EnumerationArea.objects.filter(locations=self.kampala))

        ea.locations.add(self.wakiso)
        self.assertEqual(2, ea.locations.all().count())