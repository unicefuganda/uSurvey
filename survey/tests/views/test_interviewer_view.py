import json
from model_mommy import mommy
from django.test.client import Client
from mock import *
from django.contrib.auth.models import User, Group
from survey.models.users import UserProfile
from survey.tests.base_test import BaseTest
from survey.forms.interviewer import InterviewerForm,\
    USSDAccessForm, ODKAccessForm
from survey.models import EnumerationArea
from survey.models import LocationType, Location, Survey
from survey.models import Interviewer
from survey.models import USSDAccess
from django.forms.models import inlineformset_factory
from django.core.urlresolvers import reverse


class InterviewerViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.user_without_permission = User.objects.create_user(
            username='useless', email='demo5@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user(
            'demo5', 'demo5@kant.com', 'demo5'), 'can_view_interviewers')
        self.assign_permission_to(self.raj, 'can_view_interviewers')
        self.client.login(username='demo5', password='demo5')
        self.ea = EnumerationArea.objects.create(name="BUBEMBE", code="11-BUBEMBE")
        self.country_type = LocationType.objects.create(name="country", slug="country")
        self.country = self.country_type
        self.district = LocationType.objects.create(name="Kampala", slug="kampala", parent=self.country_type)
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(name="Kampala", type=self.district, parent=self.uganda)
        self.ea.locations.add(self.kampala)
        self.survey = Survey.objects.create(name="survey A")
        self.form_data = {
            'name': 'Interviewer_1',
            'date_of_birth': '1987-08-06',
            'gender': 1,
            'ea':self.ea       
        }

    def test_unblock_interviwer_details(self):
        investigator = Interviewer.objects.create(name="Investigator6",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')        
        response = self.client.get(reverse('unblock_interviewer_page', kwargs={'interviewer_id': investigator.id}))
        self.assertIn(response.status_code, [302, 200])
        investigator = Interviewer.objects.get(name='Investigator6')
        self.assertEquals(investigator.is_blocked, False)
        # self.assertIn("Interviewer USSD Access successfully unblocked.", response.cookies['messages'].value)        
        # self.assertRedirects(response, expected_url=reverse('interviewers_page'), msg_prefix='')

    def test_block_interviewer_details(self):
        investigator = Interviewer.objects.create(name="Investigator5",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')        
        response = self.client.get(reverse('block_interviewer_page', kwargs={'interviewer_id':investigator.id}))
        self.assertIn(response.status_code, [302,200])
        z3 = Interviewer.objects.get(name='Investigator5')
        self.assertEquals(z3.is_blocked, True)
        # self.assertIn("Interviewer USSD Access successfully blocked.", response.cookies['messages'].value)
        # self.assertRedirects(response, expected_url=reverse('interviewers_page'))

    def test_block_interviwer_when_no_such_interviewer_exist(self):
        url = reverse('block_interviewer_page', kwargs={"interviewer_id":  99999})
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=reverse('interviewers_page'))
        self.assertIn("Interviewer does not exist.", response.cookies['messages'].value)

    def test_block_interviwer_when_no_such_interviewer_exist(self):
        url = reverse('unblock_interviewer_page', kwargs={"interviewer_id":  99999})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_get_interviewer_pages(self):
        """49, 73-75, 119, 122, 125, 139, 144-146, 154-155, 169-170, 192-193, 204-205, 216-217, 228-229

        :return:
        """
        interviewer = mommy.make(Interviewer, ea=self.ea)
        url = reverse('interviewer_completion_summary', args=(interviewer.id, ))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)
        url = reverse("new_interviewer_page")
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('ussd_access_form', response.context)
        self.assertIn('odk_access_form', response.context)
        url = reverse("show_interviewer_page", args=(interviewer.id, ))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertIn('interviewer', response.context)


    # def test_download_interviewers(self):
    #     response = self.client.get(reverse('download_interviewers'))
    #     # self.failUnlessEqual(response.status_code, 200)
    #     self.assertIn(response.status_code, [200,302])
    #     rtype = response.headers.get('content_type')
    #     self.assertIn('text/csv', rtype)
    #     res_csv = 'attachment; \
    #     filename="%s.csv"' % filename
    #     self.assertIn(response['Content-Disposition'], res_csv)

    # def test_view_interviewer_details_when_no_such_interviewer_exists(self):
    #     investigator = Interviewer.objects.create(name="Investigator10",
    #                                                    ea=self.ea,
    #                                                    gender='1', level_of_education='Primary',
    #                                                    language='Eglish', weights=0,date_of_birth='1987-01-01')
    #     self.client.get(reverse('view_interviewer_page', kwargs={"interviewer_id":investigator.id}))
    #     self.assertIn(response.status_code, [200,302])
        # url = reverse(
        #     'view_interviewer_page',
        #     kwargs={"interviewer_id":  investigator.id})
        # response = self.client.get(url)
        # self.assertRedirects(response, expected_url=reverse('interviewers_page'))
        # self.assertIn("Interviewer not found.", response.cookies['messages'].value)

    def test_restricted_permission(self):
        investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')
        self.assert_restricted_permission_for(reverse('interviewers_page'))
        # url = reverse('view_interviewer_page', kwargs={"interviewer_id":  investigator.id,"mode":'view'})
        # self.assert_restricted_permission_for(reverse(url))
        # url = reverse('block_interviewer_page', kwargs={"interviewer_id":  investigator.id})
        # self.assert_restricted_permission_for(reverse(url))
        # url = reverse('unblock_interviewer_page', kwargs={"interviewer_id":  investigator.id})
        # self.assert_restricted_permission_for(reverse(url))
        # url = reverse('download_interviewers')
        # self.assert_restricted_permission_for(reverse(url))