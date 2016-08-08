from django.test import Client
from mock import patch
from django.contrib.auth.models import User
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition

from survey.forms.group_condition import GroupConditionForm

from survey.forms.household_member_group import HouseholdMemberGroupForm
from survey.tests.base_test import BaseTest
from survey.views.household_member_group import has_valid_condition


class GroupConditionViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_household_groups')
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
        self.assertIn('New Criteria', response.context['title'])
        self.assertIn('/conditions/new/', response.context['action'])

    def test_duplicate_condition_shows_error_on_views(self):
        data = {'attribute': 'AGE',
                'condition': 'EQUALS',
                'value': '8'}
        GroupCondition.objects.create(**data)
        response = self.client.post('/conditions/new/', data=data)
        error_message = 'Condition not added: Group condition with this Value, Attribute and Condition already exists.'
        self.assertTrue(error_message in response.cookies['messages'].value)
        self.assertEqual(1, GroupCondition.objects.filter(**data).count())
        self.assertRedirects(response, expected_url='/conditions/new/', status_code=302, target_status_code=200,
                             msg_prefix='')

    def test_post_condtion_form(self):
        data = {'attribute': 'AGE',
                'condition': 'EQUALS',
                'value': '8'}

        self.failIf(GroupCondition.objects.filter(**data))
        response = self.client.post('/conditions/new/', data=data)
        self.assertRedirects(response, expected_url='/conditions/', status_code=302, target_status_code=200,
                             msg_prefix='')
        self.assertEquals(1, len(GroupCondition.objects.filter(**data)))
        success_message = 'Condition successfully added.'
        self.assertTrue(success_message in response.cookies['messages'].value)

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/conditions/new/')
        self.assert_restricted_permission_for('/conditions/')
        self.assert_restricted_permission_for('/conditions/1/delete/')
        
    def test_delete_condition(self):       
        condition_1 = GroupCondition.objects.create(value="some string")
        group = HouseholdMemberGroup.objects.create(order=1, name="group 1")
        condition_1.groups.add(group)
        response = self.client.get('/conditions/%s/delete/'%condition_1.id)
        retrieved_condition = GroupCondition.objects.filter(id=condition_1.id)
        self.failIf(retrieved_condition)
        self.assertEqual(0, group.conditions.all().count())
        self.assertRedirects(response, expected_url='/conditions/', status_code=302, target_status_code=200, msg_prefix='')
        success_message = 'Criteria successfully deleted.'
        self.assertIn(success_message, response.cookies['messages'].value)

class HouseholdMemberGroupTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_investigators')
        raj = self.assign_permission_to(raj, 'can_view_household_groups')
        self.client.login(username='Rajni', password='I_Rock')

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
        self.assertEquals("Create", response.context['button_label'])
        self.assertEquals("add_group_form", response.context['id'])
        self.assertEquals("/groups/new/", response.context['action'])
        self.assertIsInstance(response.context['condition_form'], GroupConditionForm)
        self.assertEquals("New Eligibility Criteria", response.context['condition_title'])

    @patch('django.contrib.messages.success')
    def test_add_group_post(self, mock_success):
        hmg_1 = GroupCondition.objects.create(value="some string")
        hmg_2 = GroupCondition.objects.create(value="another value")
        data = {'name': 'aged between 15 and 49',
                'order': 1,
                'conditions': hmg_1.id}

        self.failIf(HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order']))
        response = self.client.post('/groups/new/', data=data)
        retrieved_group = HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order'])
        self.assertEquals(1, len(retrieved_group))
        associated_conditions = retrieved_group[0].conditions.all()
        self.assertEquals(1, len(associated_conditions))
        self.assertEquals(hmg_1, associated_conditions[0])

        assert mock_success.called

    def test_add_group_with_non_existing_condition(self):
        GroupCondition.objects.all().delete()
        some_irrelevant_number = '1'
        data = {'name': 'aged between 15 and 49',
                'order': 1,
                'conditions': some_irrelevant_number}

        response = self.client.post('/groups/new/', data=data)
        self.assertEqual(200, response.status_code)
        retrieved_group = HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order'])
        self.failIf(retrieved_group)

    def test_add_group_with_already_existing_group(self):
        hmg_1 = GroupCondition.objects.create(value="some string")
        some_irrelevant_number = '1'
        data = {'name': 'aged between 15 and 49',
                'order': 1,
                'conditions': [hmg_1.id]}
        group = HouseholdMemberGroup.objects.create(name=data['name'], order=data['order'])
        self.failUnless(group.id)
        response = self.client.post('/groups/new/', data=data)
        self.assertEqual(200, response.status_code)
        associated_conditions = group.conditions.all()
        self.failIf(associated_conditions)

    def test_has_valid_condition_successes(self):
        condition = GroupCondition.objects.create(condition="EQUALS")
        self.assertTrue(has_valid_condition({'conditions': str(condition.id)}))

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
        data = {'attribute': 'AGE',
                'condition': 'EQUALS',
                'value': '9'}

        self.failIf(GroupCondition.objects.filter(**data))
        self.client.post('/conditions/new/', data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.failUnless(GroupCondition.objects.filter(**data))

    def test_ajax_call_should_return_condition_list_in_context(self):
        data = {'attribute': 'AGE',
                'condition': 'EQUALS',
                'value': '9'}

        response = self.client.post('/conditions/new/', data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        condition = GroupCondition.objects.get(**data)
        data = "%s > %s > %s" % (condition.attribute, condition.condition, condition.value)
        expected = '{"id": %s, "value": "%s"}' % (condition.id, data)
        self.assertEquals(str(expected),response.content)

    def test_save_multiple_conditions(self):
        hmg_1 = GroupCondition.objects.create(value="some string")
        hmg_2 = GroupCondition.objects.create(value="another value")
        data = {'name': 'aged between 15 and 49',
                'order': '2',
                'conditions': [int(hmg_1.id), int(hmg_2.id)]}

        self.failIf(HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order']))
        self.client.post('/groups/new/', data=data)
        retrieved_group = HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order'])
        self.assertEquals(1, len(retrieved_group))
        associated_conditions = retrieved_group[0].conditions.all()
        self.assertEquals(2, len(associated_conditions))
        self.assertIn(hmg_1, associated_conditions)
        self.assertIn(hmg_2, associated_conditions)

    def test_view_conditions_assigned_to_agroup(self):
        hmg_1 = GroupCondition.objects.create(value="condition1")
        hmg_2 = GroupCondition.objects.create(value="condition2")
        hmg_3 = GroupCondition.objects.create(value="condition3")
        group = HouseholdMemberGroup.objects.create(name='some name', order=1)

        self.failIf(group.conditions.all())
        hmg_1.groups.add(group)
        hmg_2.groups.add(group)

        response = self.client.get('/groups/%s/' % str(group.pk))
        self.assertEquals(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn("household_member_groups/conditions/index.html", templates)
        self.assertIn(hmg_1, response.context['conditions'])
        self.assertIn(hmg_2, response.context['conditions'])
        self.assertNotIn(hmg_3, response.context['conditions'])
        self.assertEqual(group, response.context['group'])

    def test_view_returns_no_conditions_message_if_no_conditions_on_a_group(self):
        group = HouseholdMemberGroup.objects.create(name='some name', order=1)

        self.failIf(group.conditions.all())

        response = self.client.get('/groups/%s/' % str(group.pk))
        # self.assertRedirects(response, expected_url='/groups/', status_code=302, target_status_code=200, msg_prefix='')
        self.assertTrue("No conditions in this group.", response.cookies['messages'].value)


    def test_restricted_permissions_for_group_details(self):
        group = HouseholdMemberGroup.objects.create(name='some name', order=1)
        self.assert_restricted_permission_for('/groups/%s/' % str(group.pk))
        self.assert_restricted_permission_for('/groups/%s/delete/' % group.id)
        self.assert_restricted_permission_for('/groups/%s/edit/' % group.id)

    def test_restricted_permissions_for_add_group(self):
        self.assert_restricted_permission_for('/groups/new/')

    def test_add_new_condition_to_group_should_get_a_condition_form(self):
        group = HouseholdMemberGroup.objects.create(name='some name', order=1)
        response = self.client.get('/groups/%d/conditions/new/' % group.id)
        self.assertEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member_groups/conditions/new.html', templates)
        self.assertIsInstance(response.context['condition_form'], GroupConditionForm)
        self.assertIn('add-condition-to-group-form', response.context['id'])
        self.assertIn('Create', response.context['button_label'])
        self.assertIn('New Criteria', response.context['title'])
        self.assertIn('/groups/%d/conditions/new/' % group.id, response.context['action'])

    def test_add_condition_to_group_adds_the_condition_to_that_groups_conditions(self):
        group = HouseholdMemberGroup.objects.create(name='some name', order=1)

        data = {'attribute': 'AGE',
                'condition': 'EQUALS',
                'value': '9'}

        response = self.client.post('/groups/%s/conditions/new/' % group.id, data=data)
        condition = GroupCondition.objects.filter(**data)
        self.failUnless(condition)
        self.assertTrue(group in condition[0].groups.all())
        self.assertRedirects(response, expected_url='/groups/%s/' %group.id, status_code=302, target_status_code=200, msg_prefix='')
        success_message = "Criteria successfully added."
        self.assertTrue(success_message in response.cookies['messages'].value)

    def test_add_condition_to_group_with_non_existing_group_raises_group_does_not_exist(self):
        data = {'attribute': 'AGE',
                'condition': 'EQUALS',
                'value': '9'}

        NON_EXISTING_GROUP_ID = 44

        response = self.client.post('/groups/%s/conditions/new/' % NON_EXISTING_GROUP_ID, data=data)
        condition = GroupCondition.objects.filter(**data)
        self.failIf(condition)
        # self.assertRedirects(response, expected_url='/groups/', status_code=302, target_status_code=200, msg_prefix='')
        error_message = "Group does not exist."
        self.assertTrue(error_message in response.cookies['messages'].value)

    def test_restricted_permissions_for_add_condition_to_group(self):
        group = HouseholdMemberGroup.objects.create(name='some name', order=1)
        self.assert_restricted_permission_for('/groups/%s/conditions/new/' % str(group.pk))

    def test_post_condtion_form(self):

        data = {'attribute': 'AGE',
                'condition': 'EQUALS',
                'value': '8'}

        GroupCondition.objects.create(**data)
        self.failUnless(GroupCondition.objects.filter(**data))
        response = self.client.post('/conditions/new/', data=data)
        self.assertRedirects(response, expected_url='/conditions/new/', status_code=302, target_status_code=200,
                             msg_prefix='')

    def test_edit_group(self):
       condition_1 = GroupCondition.objects.create(value="some string")
       condition_2 = GroupCondition.objects.create(value="5")
       group = HouseholdMemberGroup.objects.create(order=1, name="group 1")
       condition_1.groups.add(group)
       condition_2.groups.add(group)
       response = self.client.get('/groups/%s/edit/'%group.id)
       self.assertEqual(200, response.status_code)
       templates = [template.name for template in response.templates]
       self.assertIn('household_member_groups/new.html', templates)
       self.assertIsInstance(response.context['groups_form'], HouseholdMemberGroupForm)
       self.assertIn(condition_1, response.context['conditions'])
       self.assertIn(condition_2, response.context['conditions'])
       self.assertEquals("Edit Group", response.context['title'])
       self.assertEquals("Save", response.context['button_label'])
       self.assertEquals("add_group_form", response.context['id'])
       self.assertEquals("/groups/%s/edit/" % group.id, response.context['action'])
       self.assertIsInstance(response.context['condition_form'], GroupConditionForm)
       self.assertEquals("New Criteria", response.context['condition_title'])

    def test_edit_group_post(self):
       condition_1 = GroupCondition.objects.create(value="some string")
       condition_2 = GroupCondition.objects.create(value="5")
       condition_3 = GroupCondition.objects.create(value="4")
       group = HouseholdMemberGroup.objects.create(order=1, name="group 1")
       condition_1.groups.add(group)
       condition_2.groups.add(group)
       data = {'name': 'aged between 15 and 49',
               'order': 1,
               'conditions': [condition_2.id, condition_3.id]}

       response = self.client.post('/groups/%s/edit/'%group.id, data=data)
       retrieved_group = HouseholdMemberGroup.objects.filter(name=data['name'], order=data['order'])
       self.assertEquals(1, len(retrieved_group))
       associated_conditions = retrieved_group[0].conditions.all()
       self.assertEquals(2, len(associated_conditions))
       self.assertIn(condition_3, associated_conditions)
       self.assertIn(condition_2, associated_conditions)
       success_message = "Group successfully edited."
       self.assertTrue(success_message in response.cookies['messages'].value)

       self.assertRedirects(response, expected_url='/groups/%s/'%group.id, status_code=302, target_status_code=200, msg_prefix='')

    def test_delete_group(self):
        condition_1 = GroupCondition.objects.create(value="some string")
        condition_2 = GroupCondition.objects.create(value="5")
        condition_3 = GroupCondition.objects.create(value="4")
        group = HouseholdMemberGroup.objects.create(order=1, name="group 1")
        condition_1.groups.add(group)
        condition_2.groups.add(group)
        response = self.client.get('/groups/%s/delete/'%group.id)
        retrieved_group = HouseholdMemberGroup.objects.filter(name=group.name, order=group.order)
        self.failIf(retrieved_group)
        all_conditions = GroupCondition.objects.all()
        conditions_for_deleted_group = [condition_1, condition_2, condition_3]
        [self.assertIn(condition, all_conditions) for  condition in conditions_for_deleted_group]
        [self.assertNotIn(group, condition.groups.all()) for condition in conditions_for_deleted_group]
        success_message = 'Group successfully deleted.'
        self.assertIn(success_message, response.cookies['messages'].value)
