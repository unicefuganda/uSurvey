from django.test import TestCase
from django.test.client import Client
from survey.models import GroupCondition, HouseholdMemberGroup


class GroupConditionViewTest(TestCase):

    def test_view_conditions_list(self):
        hmg_1 = GroupCondition.objects.create(value="some string")
        hmg_2 = GroupCondition.objects.create(value="5")
        client = Client()
        response = client.get('/conditions/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member_groups/conditions.html', templates)
        self.assertIn(hmg_1, response.context['conditions'])
        self.assertIn(hmg_2, response.context['conditions'])
        self.assertIsNotNone(response.context['request'])

class HouseholdMemberGroupTest(TestCase):

    def test_view_groups_list(self):
        hmg_1 = HouseholdMemberGroup.objects.create(name="group 1", order=1)
        hmg_2 = HouseholdMemberGroup.objects.create(name="group 2", order=2)
        client = Client()
        response = client.get('/groups/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('household_member_groups/index.html', templates)
        self.assertIn(hmg_1, response.context['groups'])
        self.assertIn(hmg_2, response.context['groups'])            
        self.assertIsNotNone(response.context['request'])
