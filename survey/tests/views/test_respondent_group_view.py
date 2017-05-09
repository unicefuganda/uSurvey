import json

from django.test.client import Client
from mock import *
from django.contrib.auth.models import User, Group
from survey.models import RespondentGroup, ParameterTemplate, RespondentGroupCondition

from survey.tests.base_test import BaseTest

from survey.forms.respondent_group import GroupForm
from django.core.urlresolvers import reverse


class RespondentViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.user_without_permission = User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user(
            'Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_users')
        self.client.login(username='Rajni', password='I_Rock')

    def test_new(self):
        response = self.client.get(reverse('new_respondent_groups_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('respondent_groups/new.html', templates)
        self.assertEquals(response.context['action'], reverse('new_respondent_groups_page'))
        self.assertEquals(response.context['id'], 'add_group_form')
        self.assertEquals(response.context['button_label'], 'Create')
        self.assertIsInstance(response.context['groups_form'], GroupForm)
        self.assertEqual(response.context['title'], 'New Group')

    def test_index(self):
        response = self.client.get(reverse('respondent_groups_page'))
        self.failUnlessEqual(response.status_code, 200)

    def test_list_groups(self):
        g = RespondentGroup.objects.create(name='g1',description='des')
        response = self.client.get(reverse('respondent_groups_page'))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('respondent_groups/index.html', templates)
        self.assertIn(g, response.context['groups'])
        self.assertNotEqual(None, response.context['request'])

    def test_edit_group_view(self):
        g = RespondentGroup.objects.create(name='g1',description='des')
        url = reverse(
            'respondent_groups_edit',
            kwargs={"group_id":  str(g.pk), "mode":  "edit"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('respondent_groups/new.html', templates)
        self.assertEquals(response.context['action'], url)
        self.assertEquals(response.context['id'], 'add_group_form')
        self.assertEquals(response.context['title'], 'Edit Group')
        self.assertEquals(response.context['button_label'], 'Save')
        self.assertIsInstance(response.context['group_form'], GroupForm)

    def test_group_does_not_exist(self):
        message = "Group does not exist."
        self.assert_object_does_not_exist(reverse('respondent_groups_edit',kwargs={"group_id":500}), message)

    def test_should_throw_error_if_deleting_non_existing_group(self):
        message = "Group does not exist."
        self.assert_object_does_not_exist(reverse('respondent_groups_delete',kwargs={"group_id":500}), message)