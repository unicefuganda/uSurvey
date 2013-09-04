from django.test import TestCase
from django.test.client import Client
from survey.models import GroupCondition, HouseholdMemberGroup
from survey.forms.group_condition import GroupConditionForm
from survey.forms.household_member_group import HouseholdMemberGroupForm
from mock import patch
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from survey.tests.base_test import BaseTest
from survey.views.household_member_group import has_valid_condition


class GroupConditionViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
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
        data = {'attribute': 'rajni',
                'condition': 'EQUALS',
                'value': 'kant'}

        self.failIf(GroupCondition.objects.filter(**data))
        response = self.client.post('/conditions/new/', data=data)
        self.assertRedirects(response, expected_url='/conditions/', status_code=302, target_status_code=200,
                             msg_prefix='')
        self.assertEquals(1, len(GroupCondition.objects.filter(**data)))
        assert mock_success.called

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/conditions/new/')
        self.assert_restricted_permission_for('/conditions/')


class HouseholdMemberGroupTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_investigators')
        raj = self.assign_permission_to(raj, 'can_view_batches')
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

    def test_add_group(self):
        hmg_1 = GroupCondition.objects.create(value="some string")
        hmg_2 = GroupCondition.objects.create(value="5")
        response = self.client.get('/groups/new/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member_groups/new.html', templates)
        self.assertIsInstance(response.context['groups_form'], HouseholdMemberGroupForm)
        self.assertIn(hmg_1, response.context['conditions'])
        self.assertIn(hmg_2, response.context['conditions'])
        self.assertEquals("New Group", response.context['title'])
        self.assertEquals("Save", response.context['button_label'])
        self.assertEquals("add_group_form", response.context['id'])
        self.assertEquals("/groups/new/", response.context['action'])
        self.assertIsInstance(response.context['condition_form'], GroupConditionForm)
        self.assertEquals("New Condition", response.context['condition_title'])


    @patch('django.contrib.messages.success')
    def test_add_group_post(self, mock_success):
        hmg_1 = GroupCondition.objects.create(value="some string")
        data = {'name': 'aged between 15 and 49',
                'order': 1,
                'condition': hmg_1.id}

        self.failIf(HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order']))
        response = self.client.post('/groups/new/', data=data)
        retrieved_group = HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order'])
        self.assertEquals(1, len(retrieved_group))
        associated_conditions = retrieved_group[0].conditions.all()
        self.assertEquals(1, len(associated_conditions))
        self.assertEquals(hmg_1, associated_conditions[0].group_condition)

        self.assertRedirects(response, expected_url='/groups/', status_code=302, target_status_code=200, msg_prefix='')
        assert mock_success.called

    def test_add_group_with_non_existing_condition(self):
        GroupCondition.objects.all().delete()
        some_irrelevant_number = '1'
        data = {'name': 'aged between 15 and 49',
                'order': 1,
                'condition': some_irrelevant_number}

        response = self.client.post('/groups/new/', data=data)
        self.assertEqual(200, response.status_code)
        retrieved_group = HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order'])
        self.failIf(retrieved_group)

    def test_add_group_with_already_existing_group(self):
        hmg_1 = GroupCondition.objects.create(value="some string")
        some_irrelevant_number = '1'
        data = {'name': 'aged between 15 and 49',
                'order': 1,
                'condition': hmg_1.id}
        group = HouseholdMemberGroup.objects.create(name=data['name'], order=data['order'])
        self.failUnless(group.id)
        response = self.client.post('/groups/new/', data=data)
        self.assertEqual(200, response.status_code)
        associated_conditions = group.conditions.all()
        self.failIf(associated_conditions)

    def test_has_valid_condition_successes(self):
        condition = GroupCondition.objects.create(condition="EQUALS")
        self.assertTrue(has_valid_condition({'condition': str(condition.id)}))

    def test_has_valid_condition_fails_when_there_is_no_corresponding_condition(self):
        some_invalid_condition_id = '1'
        GroupCondition.objects.filter(id=some_invalid_condition_id).delete()
        self.assertFalse(has_valid_condition({'condition': some_invalid_condition_id}))

    def test_has_valid_condition_fails_when_condition_id_is_not_posted(self):
        self.assertFalse(has_valid_condition({'some_irrelevant_key': '1'}))

    def test_has_valid_condition_fails_when_condition_id_is_NaN(self):
        self.assertFalse(has_valid_condition({'condition': 'not a number'}))
        self.assertFalse(has_valid_condition({'condition': ""}))

    def test_ajax_call_to_new_should_save_the_object(self):
        data = {'attribute': 'rajni',
                'condition': 'EQUALS',
                'value': 'kant'}

        self.failIf(GroupCondition.objects.filter(**data))
        response = self.client.post('/conditions/new/', data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.failUnless(GroupCondition.objects.filter(**data))

    def test_ajax_call_should_return_condition_list_in_context(self):
        data = {'attribute': 'rajni',
                'condition': 'EQUALS',
                'value': 'kant'}

        response = self.client.post('/conditions/new/', data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        condition = GroupCondition.objects.get(**data)
        data = "%s > %s > %s" % (condition.attribute, condition.condition, condition.value)
        expected = '{"id": %s, "value": "%s"}' % (condition.id, data)
        self.assertEquals(str(expected),response.content)
        
    def test_save_multiple_conditions(self):
        hmg_1 = GroupCondition.objects.create(value="some string")
        hmg_2 = GroupCondition.objects.create(value="some string")
        print hmg_1.id
        print hmg_2.id
        data = {'name': 'aged between 15 and 49',
                'order': 1,
                'condition': [hmg_1.id, hmg_2.id]}

        self.failIf(HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order']))
        response = self.client.post('/groups/new/', data=data)
        retrieved_group = HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order'])
        self.assertEquals(1, len(retrieved_group))
        associated_conditions = retrieved_group[0].conditions.all()
        self.assertEquals(2, len(associated_conditions))
        
        