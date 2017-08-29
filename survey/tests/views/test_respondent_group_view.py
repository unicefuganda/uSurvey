import json

from django.test.client import Client
from mock import *
from django.contrib.auth.models import User, Group
from survey.models import RespondentGroup, ParameterTemplate, RespondentGroupCondition

from survey.tests.base_test import BaseTest

from survey.forms.respondent_group import GroupForm, RespondentGroupCondition
from django.core.urlresolvers import reverse


class RespondentViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.user_without_permission = User.objects.create_user(
            username='useless', email='demo11@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user(
            'demo11', 'demo11@kant.com', 'demo11'), 'can_view_users')
        self.client.login(username='demo11', password='demo11')
        self.form_data = {"name":'G-1',"description":"blah blah"}

    def test_new(self):
        response = self.client.get(reverse('new_respondent_groups_page'))        
        self.assertEqual(200, response.status_code)          
        templates = [template.name for template in response.templates]
        self.assertIn('respondent_groups/new.html', templates)
        self.assertEquals(response.context['action'], reverse('new_respondent_groups_page'))
        self.assertEquals(response.context['id'], 'add_group_form')
        self.assertEquals(response.context['button_label'], 'Create')
        self.assertIsInstance(response.context['groups_form'], GroupForm)
        self.assertEqual(response.context['title'], 'New Group')

    def test_index(self):
        g = RespondentGroup.objects.create(name='g111',description='des')
        groups = RespondentGroup.objects.all()
        response = self.client.get(reverse('respondent_groups_page'))
        self.assertEquals(response.status_code, 200)
        self.assertIn(groups, response.context['groups'])
        

    def test_list_groups(self):
        g = RespondentGroup.objects.create(name='g1',description='des')
        response = self.client.get(reverse('respondent_groups_page'))
        self.assertEquals(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('respondent_groups/index.html', templates)
        self.assertIn(g, response.context['groups'])
        self.assertNotEqual(None, response.context['request'])

    def test_edit_group_view(self):
        g = RespondentGroup.objects.create(name='g1',description='des')
        url = reverse(
            'respondent_groups_edit',
            kwargs={"group_id": g.pk})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
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


    @patch('django.contrib.messages.success')
    def test_create_group_onpost(self, success_message):
        form_data = self.form_data
        g = RespondentGroup.objects.filter(name=form_data['name'])
        self.failIf(g)
        response = self.client.post(reverse('new_respondent_groups_page'), data=form_data)
        self.assertEquals(response.status_code, 302)
        self.rsp = RespondentGroup.objects.create(name="G-1", description="blah blah")
        g = RespondentGroup.objects.get(name=self.rsp)
        self.failUnless(g.id)
        for key in ['name','description']:
            value = getattr(g, key)
            self.assertEqual(form_data[key], str(value))

        glist = Interviewer.objects.filter(name=g)
        self.failUnless(glist)
        self.assertEquals(
            glist[0].description, form_data['description'])
        assert success_message.called

    @patch('django.contrib.messages.warning')
    def test_failure_group_onpost(self, success_message):
        form_data = self.form_data
        form_data['name']  = ''
        response = self.client.post(reverse('new_respondent_groups_page'), data=form_data)
        self.assertEqual(response.status_code, 302)
        assert success_message.called

    def test_restricted_permission(self):
        self.assert_restricted_permission_for(reverse('new_respondent_groups_page'))
        self.assert_restricted_permission_for(reverse('respondent_groups_page'))
        url = reverse('respondent_groups_edit',kwargs={"group_id":500})
        self.assert_restricted_permission_for(url)

    def test_delete_should_delete_the_group(self):
        g = RespondentGroup.objects.create(**self.form_data)
        self.failUnless(g)
        url = reverse('respondent_groups_delete',kwargs={"group_id":g.id})
        response = self.client.get(url)

        # self.assertRedirects(
        #     response, reverse('respondent_groups_page'), status_code=302, target_status_code=200, msg_prefix='')
        self.assertRedirects(response, expected_url=reverse('respondent_groups_page'), status_code=302,
                             target_status_code=200, msg_prefix='')

    def test_should_throw_error_if_deleting_non_existing_group(self):
        message = "Group does not exist."
        url = reverse('respondent_groups_delete',kwargs={"group_id":500})
        self.assert_object_does_not_exist(url, message)


    def test_delete_should_delete_the_groupcondition(self, success_message):
        rg = RespondentGroup.objects.create(name='rg1_c', description='blah')
        p = ParameterTemplate.objects.create(id=1)
        self.failUnless(p.id)
        p = ParameterTemplate.objects.all()[0]
        rgc = RespondentGroupCondition.objects.create(respondent_group_id=rg,test_question=p.id,validation_test='abcd')
        g = RespondentGroup.objects.get(name='rg1_c')
        self.failUnless(rgc.id)
        self.failUnless(g.id)
        url = reverse('delete_condition_page',kwargs={"condition_id":rgc.id})
        response = self.client.get(url)
        self.assertRedirects(
            response, reverse('respondent_groups_page'), status_code=302, target_status_code=200, msg_prefix='')
    
    def test_should_throw_error_if_deleting_non_existing_groupcondition(self):
        message = "Group does not exist."
        url = reverse('delete_condition_page',kwargs={"condition_id":99999})
        self.assert_object_does_not_exist(url, message)

    