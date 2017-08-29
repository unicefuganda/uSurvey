import json

from django.test.client import Client
from mock import *
from django.template.defaultfilters import slugify
from survey.models.locations import *
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from survey.models import Backend, EnumerationArea, Survey, ODKAccess, USSDAccess
from survey.models.interviewer import Interviewer
from survey.tests.base_test import BaseTest
from survey.forms.interviewer import InterviewerForm
# from survey.models.formula import *


class InvestigatorsViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_interviewers')
        self.client.login(username='Rajni', password='I_Rock')

        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.district = LocationType.objects.create(
            name='District', slug='district', parent=self.country)
        self.city = LocationType.objects.create(
            name='City', slug='city', parent=self.district)
        self.village = LocationType.objects.create(
            name='Village', slug='village', parent=self.city)

        self.uganda = Location.objects.create(name='Uganda', type=self.country)

        self.kampala = Location.objects.create(
            name='Kampala', parent=self.uganda, type=self.district)
        self.abim = Location.objects.create(
            name='Abim', parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(
            name='Kampala City', parent=self.kampala, type=self.city)
        self.kampala_city_village = Location.objects.create(name='Kampala City Vllage', parent=self.kampala_city,
                                                            type=self.village)
        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.kampala_city_village)
        self.survey = Survey.objects.create(name='test survey')

# new_interviewer_page

    def test_create_investigators_success(self):
        ea = self.ea
        survey = self.survey
        backend = Backend.objects.create(name='something')
        form_data = {
            'name': 'Rajini823',
            'gender': '1',
            'date_of_birth': "04-09-1979",
            'level_of_education': 'Nursery',
            'language': 'Luganda',
            'country': self.uganda.id,
            'ea': ea.id,
            'survey': survey.pk,
            'user_identifier': 'chigo',
            'is_active': 'on',
            'odk_token': '12345',
            'ussd_access-TOTAL_FORMS': '1',
            'ussd_access-INITIAL_FORMS': '0',
            'ussd_access-MAX_FORMS': '1000',
            'ussd_access-MIN_FORMS': '0',
            'ussd_access-0-intervieweraccess_ptr': '',
            'ussd_access-0-interviewer': '',
            'ussd_access-0-user_identifier': '',
            'ussd_access-0-is_active': 'on',
            'ussd_access-0-DELETE': '',
            'save_button': ''

        }
        response = self.client.post(
            reverse('new_interviewer_page'), data=form_data)
        accesses = ODKAccess.objects.filter(
            user_identifier=form_data['user_identifier'])
        # self.assertTrue(response.path.endswith('login'))
        self.assertEquals(accesses.count(), 1)
        self.assertEquals(accesses[0].interviewer.name, form_data['name'])

    def test_edit_interviewer_url(self):
        self.test_create_investigators_success()
        interviewer = Interviewer.objects.get(name='Rajini823')
        odk_access = ODKAccess.objects.get(user_identifier='chigo')
        form_data = {
            'name': 'Rajini823',
            'gender': '1',
            'date_of_birth': "04-10-1979",
            'level_of_education': 'Nursery',
            'language': 'Luganda',
            'country': self.uganda.id,
            'ea': self.ea.id,
            'survey': self.survey.pk,
            'user_identifier': 'chigo',
            'is_active': 'on',
            'odk_token': '12375',
            'ussd_access-TOTAL_FORMS': '1',
            'ussd_access-INITIAL_FORMS': '0',
            'ussd_access-MAX_FORMS': '1000',
            'ussd_access-MIN_FORMS': '0',
            'ussd_access-0-intervieweraccess_ptr': '',
            'ussd_access-0-interviewer': interviewer.pk,
            'ussd_access-0-user_identifier': '717171231',
            'ussd_access-0-is_active': 'on',
            'ussd_access-0-DELETE': '',
            'save_button': ''
        }
        response = self.client.post(
            reverse('edit_interviewer_page', args=(interviewer.pk, )), data=form_data)
        interviewer.refresh_from_db()
        odk_access.refresh_from_db()
        self.assertEquals(interviewer.date_of_birth.strftime(
            '%d-%m-%Y'), form_data['date_of_birth'])
        self.assertEquals(odk_access.odk_token, form_data['odk_token'])
        self.assertEquals(interviewer.ussd_access.count(), 1)
        self.assertEquals(interviewer.ussd_access[0].user_identifier, form_data[
                          'ussd_access-0-user_identifier'])

    def test_downlaod_interviewer(self):
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=self.ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='English')
        response = self.client.post(reverse('download_interviewers'))
        # one for header another for the interviewr details
        self.assertEquals(len(response.content.splitlines()), 2)

    def test_list_interviewers_gives_no_error(self):
        self.test_create_investigators_success()
        response = self.client.get(reverse('interviewers_page'))
        interviewers = response.context['interviewers']
        self.assertEquals(interviewers.count(), 1)
        self.assertEquals(interviewers[0].name, 'Rajini823')

    def test_block_interviewer(self):
        interviewer = Interviewer.objects.create(name="Investigator",
                                                 ea=self.ea,
                                                 gender='1', level_of_education='Primary',
                                                 language='English')
        USSDAccess.objects.create(
            interviewer=interviewer, user_identifier='717272737')
        ODKAccess.objects.create(
            interviewer=interviewer, user_identifier='ants')
        self.client.get(
            reverse('block_interviewer_odk', args=(interviewer.pk, )))
        self.assertTrue(interviewer.odk_access.filter(
            is_active=False).exists())
        self.client.get(
            reverse('block_interviewer_ussd', args=(interviewer.pk, )))
        self.assertTrue(interviewer.ussd_access.filter(
            is_active=False).exists())
        self.client.get(
            reverse('unblock_interviewer_odk', args=(interviewer.pk, )))
        self.assertTrue(interviewer.odk_access.filter(is_active=True).exists())
        self.client.get(
            reverse('unblock_interviewer_ussd', args=(interviewer.pk, )))
        self.assertTrue(interviewer.ussd_access.filter(
            is_active=True).exists())

    # def test_block_non_existing_interviewer_brings_error_message(self):
    #     response = self.client.get(
    #         reverse('block_interviewer_odk', args=(3, )))
    #     messages = response.context['messages']
    #     self.assertTrue(len(messages) > 0)
    #     self.assertEquals(messages[0].tag, 'error')
    #     self.client.get(reverse('block_interviewer_ussd', args=(3, )))
    #     messages = response.context['messages']
    #     self.assertTrue(len(messages) > 0)
    #     self.assertEquals(messages[0].tag, 'error')
    #     self.client.get(reverse('unblock_interviewer_odk', args=(6, )))
    #     messages = response.context['messages']
    #     self.assertTrue(len(messages) > 0)
    #     self.assertEquals(messages[0].tag, 'error')
    #     self.client.get(reverse('unblock_interviewer_ussd', args=(8, )))
    #     messages = response.context['messages']
    #     self.assertTrue(len(messages) > 0)
    #     self.assertEquals(messages[0].tag, 'error')
