from django.test import TestCase
from django.test.client import Client
from survey.models import GroupCondition, HouseholdMemberGroup
from survey.forms.group_condition import GroupConditionForm
from mock import patch
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from survey.tests.base_test import BaseTest

class GroupConditionViewTest(BaseTest):
    
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_batches')
        raj = self.assign_permission_to(raj, 'can_view_investigators')

        self.client.login(username='Rajni', password='I_Rock')

    def test_view_conditions_list(self):
        hmg_1 = GroupCondition.objects.create(value="some string")
        hmg_2 = GroupCondition.objects.create(value="5")
        response = self.client.get('/conditions/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member_groups/conditions/index.html', templates)
        self.assertIn(hmg_1, response.context['conditions'])
        self.assertIn(hmg_2, response.context['conditions'])
        self.assertIsNotNone(response.context['request'])
    
    def test_add_condition(self):
        response = self.client.get('/conditions/new/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member_groups/conditions/new.html', templates)
        self.assertIsInstance(response.context['condition_form'], GroupConditionForm)
        self.assertIn('add-condition-form', response.context['id'])
        self.assertIn('Save', response.context['button_label'])
        self.assertIn('New condition', response.context['title'])
        self.assertIn('/conditions/new/', response.context['action'])
    
    @patch('django.contrib.messages.success')
    def test_post_condtion_form(self, mock_success):
        data = {'attribute':'rajni',
                'condition':'EQUALS',
                'value':'kant'}
                
        self.failIf(GroupCondition.objects.filter(**data))
        response = self.client.post('/conditions/new/', data=data)
        self.assertRedirects(response, expected_url='/conditions/', status_code=302, target_status_code=200, msg_prefix='')
        self.assertEquals(1, len(GroupCondition.objects.filter(**data)))
        assert mock_success.called

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/conditions/new/')
        self.assert_restricted_permission_for('/conditions/')

class HouseholdMemberGroupTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_investigators')

        self.client.login(username='Rajni', password='I_Rock')

    def test_view_groups_list(self):
        hmg_1 = HouseholdMemberGroup.objects.create(name="group 1", order=1)
        hmg_2 = HouseholdMemberGroup.objects.create(name="group 2", order=2)
        response = self.client.get('/groups/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member_groups/index.html', templates)
        self.assertIn(hmg_1, response.context['groups'])
        self.assertIn(hmg_2, response.context['groups'])            
        self.assertIsNotNone(response.context['request'])

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/groups/')
        