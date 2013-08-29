from django.test import TestCase
from django.test.client import Client
from survey.models import *
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from survey.investigator_configs import *
from rapidsms.contrib.locations.models import Location, LocationType

class BulkSMSTest(TestCase):

    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_batches', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)
        self.client.login(username='Rajni', password='I_Rock')

        district = LocationType.objects.create(name=PRIME_LOCATION_TYPE, slug='district')
        country = LocationType.objects.create(name='Country', slug = 'country')
        self.kampala = Location.objects.create(name="Kampala", type=district)
        self.abim = Location.objects.create(name="Abim", type=district)
        uganda = Location.objects.create(name="Uganda", type=country)

    def test_get(self):
        response = self.client.get('/bulk_sms')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('bulk_sms/index.html', templates)
        self.assertEquals(len(response.context['locations']), 2)

    def test_send(self):
        response = self.client.post('/bulk_sms/send', data={'locations': [self.kampala.pk, self.abim.pk], 'text': 'text'}, follow=True)
        self.assertEquals(len(response.context['messages']), 1)
        for message in response.context['messages']:
            self.assertEquals(str(message), "Your message has been sent to investigators.")
        self.failUnlessEqual(response.status_code, 200)
        self.assertRedirects(response, 'http://testserver/bulk_sms')

    def test_send_failures(self):
        response = self.client.post('/bulk_sms/send', data={'locations': [], 'text': 'text'}, follow=True)
        self.assertEquals(len(response.context['messages']), 1)
        for message in response.context['messages']:
            self.assertEquals(str(message), "Please select a location.")
        self.failUnlessEqual(response.status_code, 200)
        self.assertRedirects(response, 'http://testserver/bulk_sms')

        response = self.client.post('/bulk_sms/send', data={'locations': [self.kampala.pk, self.abim.pk], 'text': ''}, follow=True)
        for message in response.context['messages']:
            self.assertEquals(str(message), "Please enter the message to send.")
        self.failUnlessEqual(response.status_code, 200)
        self.assertRedirects(response, 'http://testserver/bulk_sms')

    def assert_restricted_permission_for(self, url):
        self.client.logout()

        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)

        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%url, status_code=302, target_status_code=200, msg_prefix='')

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/bulk_sms')
        self.assert_restricted_permission_for('/bulk_sms/send')
