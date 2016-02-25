from django.test import TestCase
from django.test.client import Client
from rapidsms.contrib.locations.models import Location
from survey.models.locations import *
from survey.models import EnumerationArea
from survey.models.batch import Batch
from survey.models.interviewer import Interviewer


class TestApi(TestCase):
    def setUp(self):
        self.client = Client()
        self.country = LocationType.objects.create(name="Country", slug='country')
        self.district = LocationType.objects.create(name="District", parent=self.country,slug='district')
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(name="Kampala", type=self.district, parent=self.uganda)
        batch = Batch.objects.create(name="Batch", order = 1)
        batch.open_for_location(self.kampala)

    def test_create_investigator(self):
        self.assertEquals(Interviewer.objects.count(), 0)
        mobile_number = '123456789'
        response = self.client.get("/api/create_investigator", data={'mobile_number': mobile_number})
        self.failUnlessEqual(response.status_code, 200)
        investigator = Interviewer.objects.all()[0]
        self.assertEquals(investigator.households.count(), 1)
        self.assertEquals(investigator.location, self.location)

    def test_delete_investigator(self):
        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.location)
        investigator = Interviewer.objects.create(name="investigator name", mobile_number="123456789", ea=self.ea)
        self.assertEquals(Interviewer.objects.count(), 1)
        response = self.client.get("/api/delete_investigator", data={'mobile_number': investigator.mobile_number})
        self.failUnlessEqual(response.status_code, 200)
        self.assertEquals(Interviewer.objects.count(), 0)