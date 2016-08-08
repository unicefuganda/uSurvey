import json

from django.test.client import Client
from mock import *
from django.template.defaultfilters import slugify
from survey.models.locations import *
from django.contrib.auth.models import User

from django.conf import settings
from survey.models import Backend, Household, LocationTypeDetails, EnumerationArea
from survey.models.interviewer import Interviewer

from survey.tests.base_test import BaseTest

from survey.forms.interviewer import InterviewerForm
from survey.models.formula import *

class InvestigatorsViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_investigators')
        self.client.login(username='Rajni', password='I_Rock')

        self.country = LocationType.objects.create(name='Country', slug='country')
        self.district = LocationType.objects.create(name='District', slug='district')
        self.city = LocationType.objects.create(name='City', slug='city')
        self.village = LocationType.objects.create(name='Village', slug='village')

        self.uganda = Location.objects.create(name='Uganda', type=self.country)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.country)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.district)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.city)
        LocationTypeDetails.objects.create(country=self.uganda, location_type=self.village)

        self.kampala = Location.objects.create(name='Kampala', tree_parent=self.uganda, type=self.district)
        self.abim = Location.objects.create(name='Abim', tree_parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)


    def test_create_investigators_success(self):
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(self.uganda)

        backend = Backend.objects.create(name='something')
        form_data = {
            'name': 'Rajini',
            'male': 'f',
            'age': '20',
            'level_of_education': 'Nursery',
            'language': 'Luganda',
            'country': self.uganda.id,
            'ea': ea.id,
            'backend': backend.id,
            'confirm_mobile_number': '987654321',
        }
        investigator = Interviewer.objects.filter(name=form_data['name'], ea=ea,
                                                   )
        self.failIf(investigator)
        response = self.client.post('/interviewers/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 302) # ensure redirection to list investigator page

    def test_downlaod_interviewer(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        #ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        response = self.client.post('/interviewers/export/')
