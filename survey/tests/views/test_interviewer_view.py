import json

from django.test.client import Client
from mock import *
from django.contrib.auth.models import User, Group
from survey.models.users import UserProfile

from survey.tests.base_test import BaseTest

from survey.forms.interviewer import InterviewerForm,\
    USSDAccessForm, ODKAccessForm
from survey.models import EnumerationArea
from survey.models import LocationType
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
            'demo5', 'demo5@kant.com', 'demo5'), 'can_view_users')
        self.client.login(username='demo5', password='demo5')

        self.ea = EnumerationArea.objects.create(name="EA2")
        self.country = LocationType.objects.create(name="country", slug="country")
        self.kampala = Location.objects.create(name="Kampala", type=country)
        self.ea.locations.add(kampala)
        self.survey = Survey.objects.create(name="survey A")
        self.form_data = {
            'name': 'Interviewer_1',
            'date_of_birth': '1987-08-06',
            'gender': 1,
            'ea':self.ea,
            'survey':self.survey
        }

    def test_new(self):
        response = self.client.get(reverse('new_interviewer_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('interviewers/interviewer_form.html', templates)
        self.assertEquals(response.context['action'], reverse('new_interviewer_page'))
        self.assertEquals(response.context['id'], 'create-interviewer-form')
        self.assertEquals(response.context['class'], 'interviewer-form')
        self.assertEquals(response.context['button_label'], 'Save')
        self.assertEquals(response.context['loading_text'], 'Creating...')
        self.assertIsInstance(response.context['form'], InterviewerForm)
        USSDAccessFormSet = inlineformset_factory(
            Interviewer, USSDAccess, form=USSDAccessForm, extra=extra)
        ussd_access_form = USSDAccessFormSet(
            prefix='ussd_access', instance=None)
        odk_access_form = ODKAccessForm(instance=None)
        self.assertIsInstance(response.context['ussd_access_form'], ussd_access_form)
        self.assertIsInstance(response.context['odk_access_form'], odk_access_form)
        self.assertEqual(response.context['title'], 'New Interviewer')

    @patch('django.contrib.messages.success')
    def test_create_interviewer(self, success_message):
        form_data = self.form_data
        investigator = Interviewer.objects.filter(name=form_data['name'])
        self.failIf(investigator)
        response = self.client.post(reverse('new_interviewer_page'), data=form_data)
        self.failUnlessEqual(response.status_code, 302)

        investigator = Interviewer.objects.get(name=form_data['name'])
        self.failUnless(investigator.id)
        for key in ['name','gender','date_of_birth','survey','ea']:
            value = getattr(investigator, key)
            self.assertEqual(form_data[key], str(value))

        investigator = Interviewer.objects.filter(name=investigator)
        self.failUnless(investigator)
        self.assertEquals(
            investigator[0].date_of_birth, form_data['date_of_birth'])
        assert success_message.called


    def test_index(self):
        response = self.client.get(reverse('interviewers_page'))
        self.failUnlessEqual(response.status_code, 200)


    def test_list_interviewers(self):
        investigator = Interviewer.objects.create(name='int_2',survey=self.survey,ea=self.ea,date_of_birth='1987-01-01')
        response = self.client.get(reverse('interviewers_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('interviewers/index.html', templates)
        self.assertIn(investigator, response.context['interviewers'])
        self.assertNotEqual(None, response.context['request'])


    def test_edit_interviewer_view(self):
        investigator = Interviewer.objects.create(name='int_3',survey=self.survey,ea=self.ea,date_of_birth='1987-01-01')
        url = reverse(
            'view_interviewer_page',
            kwargs={"interviewer_id":  interviewer_id.pk,"mode":'edit'})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('interviewers/interviewer_form.html', templates)
        self.assertEquals(response.context['action'], url)
        self.assertEquals(response.context['id'], 'create-interviewer-form')
        self.assertEquals(response.context['class'], 'interviewer-form')
        self.assertEquals(response.context['title'], 'Edit Interviewer')
        self.assertEquals(response.context['button_label'], 'Save')
        self.assertEquals(response.context['loading_text'], 'Saving...')
        self.assertIsInstance(response.context['form'], InterviewerForm)
        USSDAccessFormSet = inlineformset_factory(
            Interviewer, USSDAccess, form=USSDAccessForm, extra=extra)
        ussd_access_form = USSDAccessFormSet(
            prefix='ussd_access', instance=investigator)
        odk_access_form = ODKAccessForm(instance=investigator.odk_access[0])
        self.assertIsInstance(response.context['ussd_access_form'], ussd_access_form)
        self.assertIsInstance(response.context['odk_access_form'], odk_access_form)
        self.assertEqual(response.context['title'], 'New Interviewer')


    def test_edit_interviewer_updates_interviewer_information(self):
        form_data = {
            'name': 'Interviewer_4',
            'date_of_birth': '1987-08-06',
            'gender': 0,
            'ea':self.ea,
            'survey':self.survey
        }
        self.failIf(Interviewer.objects.filter(name=form_data['name']))
        investigator = Interviewer.objects.create(
            name=form_data['name'],
            date_of_birth=form_data['date_of_birth'],
            gender=form_data['gender'],
            ea = self.ea,
            survey=self.survey
            )

        data = {
            'name': 'Interviewer_4',
            'date_of_birth': '1987-08-06',
            'gender': 1,
            'ea':self.ea,
            'survey':self.survey
        }
        url = reverse(
            'view_interviewer_page',
            kwargs={"interviewer_id":  interviewer_id.pk,"mode":'edit'})
        response = self.client.post(url, data=data)
        self.failUnlessEqual(response.status_code, 302)
        edited_user = Interviewer.objects.filter(name=data['name'],gender=data['gender'])
        self.assertEqual(1, edited_user.count())

    def test_view_interviewer_details(self):
        investigator = Interviewer.objects.create(name='int_5',survey=self.survey,ea=self.ea,date_of_birth='1987-01-01')
        url = reverse('view_interviewer_page', kwargs={"interviewer_id":  investigator.id,"mode":'view'})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('interviewers/interviewer_form.html', templates)
        self.assertEquals(response.context['Edit Interviewer'], user)
        self.assertEquals(
            response.context['cancel_url'],
            reverse('interviewers_page'))

    def test_unblock_interviwer_details(self):
        investigator = Interviewer.objects.create(name='int_6',survey=self.survey,ea=self.ea,date_of_birth='1987-01-01')
        url = reverse('unblock_interviewer_page', kwargs={"interviewer_id":  investigator.id})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('interviewers/index.html', templates)
        investigator = Interviewer.objects.get(name='int_6')
        self.assertEquals(investigator.is_blocked, True)
        self.assertIn("Interviewer USSD Access successfully unblocked.", response.cookies['messages'].value)
        self.assertRedirects(response, expected_url=reverse('interviewers_page'))

    def test_block_interviewer_details(self):
        investigator = Interviewer.objects.create(name='int_7',survey=self.survey,ea=self.ea,date_of_birth='1987-01-01')
        url = reverse('block_interviewer_page', kwargs={"interviewer_id":  investigator.id})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('interviewers/index.html', templates)
        investigator = Interviewer.objects.get(name='int_7')
        self.assertEquals(investigator.is_blocked, False)
        self.assertIn("Interviewer USSD Access successfully blocked.", response.cookies['messages'].value)
        self.assertRedirects(response, expected_url=reverse('interviewers_page'))

    def test_block_interviwer_when_no_such_interviewer_exist(self):
        url = reverse('block_interviewer_page', kwargs={"interviewer_id":  99999})
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=reverse('interviewers_page'))
        self.assertIn("Interviewer does not exist.", response.cookies['messages'].value)


    def test_block_interviwer_when_no_such_interviewer_exist(self):
        url = reverse('unblock_interviewer_page', kwargs={"interviewer_id":  99999})
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=reverse('interviewers_page'))
        self.assertIn("Interviewer does not exist.", response.cookies['messages'].value)
        


    def test_download_interviewers(self):
        response = self.client.get(reverse('download_interviewers'))
        self.failUnlessEqual(response.status_code, 200)
        rtype = response.headers.get('content_type')
        self.assertIn('text/csv', rtype)
        res_csv = 'attachment; \
        filename="%s.csv"' % filename
        self.assertIn(response['Content-Disposition'], res_csv)


    def test_view_interviewer_details_when_no_such_interviewer_exists(self):
        url = reverse(
            'view_interviewer_page',
            kwargs={"interviewer_id":  11111111111})
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=reverse('interviewers_page'))
        self.assertIn("Interviewer not found.", response.cookies['messages'].value)

    def test_restricted_permission(self):
        self.assert_restricted_permission_for(reverse('interviewers_page'))
        url = reverse('view_interviewer_page', kwargs={"interviewer_id":  investigator.id,"mode":'view'})
        self.assert_restricted_permission_for(reverse(url))
        url = reverse('block_interviewer_page', kwargs={"interviewer_id":  investigator.id})
        self.assert_restricted_permission_for(reverse(url))
        url = reverse('unblock_interviewer_page', kwargs={"interviewer_id":  investigator.id})
        self.assert_restricted_permission_for(reverse(url))
        url = reverse('download_interviewers')
        self.assert_restricted_permission_for(reverse(url))
