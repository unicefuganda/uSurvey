from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test.client import Client
from  urllib import quote

class BaseTest(TestCase):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')

    def assign_permission_to(self, user, permission_type='can_view_investigators'):
        some_group = Group.objects.create(name='some group that %s'% permission_type)
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename=permission_type, content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(user)
        return user

    def assert_restricted_permission_for(self, url):
        self.client.logout()
        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)
        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%quote(url), status_code=302, target_status_code=200, msg_prefix='')

    def assert_login_required(self, url):
        self.client.logout()
        response = self.client.get(url)
        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%quote(url), status_code=302, target_status_code=200, msg_prefix='')
        
    def assert_dictionary_equal(self, dict1, dict2): # needed as QuerySet objects can't be equated -- just to not override .equals
        self.assertEquals(len(dict1), len(dict2))
        dict2_keys = dict2.keys()
        for key in dict1.keys():
            self.assertIn(key, dict2_keys)
            for index in range(len(dict1[key])):
                self.assertEquals(dict1[key][index], dict2[key][index])
