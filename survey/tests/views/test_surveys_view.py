from copy import deepcopy
from django.test.client import Client
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.urlresolvers import reverse
from model_mommy import mommy
from survey.models import EnumerationArea
from survey.models import Interviewer
from survey.models import Interview, NumericalAnswer, TextAnswer, VideoAnswer
from survey.models import ListingTemplate
from survey.models import Question
from survey.models.surveys import Survey
from survey.forms.surveys import SurveyForm
from survey.tests.base_test import BaseTest
from survey.models.locations import *
from survey.models import Batch
from survey.models.users import UserProfile
from survey.utils import views_helper


class SurveyViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='demo12@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.listing_form = mommy.make(ListingTemplate)
        question1 = mommy.make(Question, qset=self.listing_form, answer_type=NumericalAnswer.choice_name())
        question2 = mommy.make(Question, qset=self.listing_form, answer_type=TextAnswer.choice_name())
        question3 = mommy.make(Question, qset=self.listing_form, answer_type=VideoAnswer.choice_name())
        self.client.login(username='demo12', password='demo12')
        self.form_data = {'name': 'survey demo12', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,
                          'random_sample_label': 'q1 {{%s}} q2: {{%s}}' % (question1.identifier, question2.identifier)}

    def test_view_survey_list(self):
        survey_1 = mommy.make(Survey)
        # survey_2 = mommy.make(Survey)
        response = self.client.get(reverse('survey_list_page'))
        self.assertEqual(200, response.status_code)
        templates = [ template.name for template in response.templates ]
        self.assertIn('surveys/index.html', templates)
        self.assertIn(survey_1, response.context['surveys'])
        # self.assertIn(survey_2, response.context['surveys'])
        self.assertIsNotNone(response.context['request'])
        self.assertIsInstance(response.context['survey_form'], SurveyForm)

    def test_add_survey(self):
        response = self.client.get(reverse('new_survey_page'))        
        self.assertEqual(200, response.status_code)
        templates = [ template.name for template in response.templates ]
        self.assertIn('surveys/new.html', templates)
        self.assertIsInstance(response.context['survey_form'], SurveyForm)
        self.assertIn('add-survey-form', response.context['id'])
        self.assertIn('Create', response.context['button_label'])
        self.assertIn('New Survey', response.context['title'])
        self.assertIn(response.context['action'], [reverse('new_survey_page'), '.'])

    def test_new_should_create_survey_on_post(self):
        user = mommy.make(UserProfile)
        form_data = deepcopy(self.form_data)
        form_data['name'] = 'new_name'
        form_data['description'] = 'edited_description'
        all_surveys = Survey.objects.filter(**self.form_data)
        self.failIf(all_surveys)
        form_data['email_group'] = user.id
        form_data['listing_form'] = self.listing_form.id
        response = self.client.post(reverse('new_survey_page'), data=form_data)
        self.assertRedirects(response, expected_url=reverse('survey_list_page'), status_code=302,
                             target_status_code=200, msg_prefix='')
        retrieved_surveys = Survey.objects.filter(name=form_data['name'])
        self.assertEquals(1, retrieved_surveys.count())
        self.assertIn('Survey successfully added.', response.cookies['messages'].__str__())

    def test_new_should_not_create_survey_on_post_if_survey_with_same_name_exists(self):
        user = mommy.make(UserProfile)
        form_data = self.form_data
        Survey.objects.create(**form_data)
        form_data['email_group'] = user.id
        response = self.client.post(reverse('new_survey_page'), data=form_data)
        error_message = 'Survey with name %s already exist.' % form_data['name']
        self.assertIn(error_message, response.context['survey_form'].errors['name'])

    def test_new_should_have_a_sample_size_of_zero_if_has_sampling_is_false(self):
        user = mommy.make(UserProfile)
        form_data = self.form_data
        form_data['has_sampling'] = False
        form_data['email_group'] = user.id
        response = self.client.post(reverse('new_survey_page'), data=form_data)
        self.assertRedirects(response, expected_url=reverse('survey_list_page'),
                             status_code=302, target_status_code=200, msg_prefix='')
        retrieved_surveys = Survey.objects.filter(name=form_data['name'], has_sampling=False)
        self.assertEquals(1, len(retrieved_surveys))
        self.assertIn('Survey successfully added.', response.cookies['messages'].__str__())
        self.assertEqual(0, retrieved_surveys[0].sample_size)

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/groups/new/')
        self.assert_restricted_permission_for('/groups/')
        self.assert_restricted_permission_for('/surveys/1/delete/')
        self.assert_restricted_permission_for('/surveys/1/edit/')

    def test_edit_should_get_form_with_data_of_the_survey(self):
        survey = Survey.objects.create(**self.form_data)
        self.failUnless(survey)
        response = self.client.get('/surveys/%d/edit/' % survey.id)
        self.assertEqual(200, response.status_code)
        templates = [ template.name for template in response.templates ]
        self.assertIn('surveys/new.html', templates)
        self.assertIsInstance(response.context['survey_form'], SurveyForm)
        self.assertIn('edit-survey-form', response.context['id'])
        self.assertIn('Save', response.context['button_label'])
        self.assertIn('Edit Survey', response.context['title'])
        self.assertIn('/surveys/%d/edit/' % survey.id, response.context['action'])

    def test_post_to_edit_page_should_edit_the_survey(self):
        survey = mommy.make(Survey, **self.form_data)
        user = mommy.make(UserProfile)
        survey.email_group.add(user)
        self.failUnless(survey)
        form_data = deepcopy(self.form_data)
        form_data['name'] = 'edited_name'
        form_data['description'] = 'edited_description'
        form_data['email_group'] = user.id
        form_data['listing_form'] = self.listing_form.id
        edit_url = reverse('edit_survey_page', args=(survey.id,))
        response = self.client.post(edit_url, data=form_data)
        self.failIf(Survey.objects.filter(name=survey.name))
        survey = Survey.objects.get(name=form_data['name'], description=form_data['description'])
        self.failUnless(survey)
        self.assertRedirects(response, '/surveys/', status_code=302, target_status_code=200, msg_prefix='')
        success_message = 'Survey successfully edited.'
        self.assertIn(success_message, response.cookies['messages'].value)

    def test_delete_should_delete_the_survey(self):
        survey = Survey.objects.create(**self.form_data)
        self.failUnless(survey)
        response = self.client.get('/surveys/%d/delete/' % survey.id)
        self.assertRedirects(response, reverse('survey_list_page'), status_code=302,
                             target_status_code=200, msg_prefix='')

    def test_should_throw_error_if_deleting_non_existing_survey(self):
        url = reverse('delete_survey', args=(390,))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)
        self.assertIn('/object_does_not_exist/', response.url)

    def test_can_delete_survey_only_if_it_has_no_interview(self):
        survey = mommy.make(Survey)
        url = reverse('delete_survey', args=(survey.id,))
        response = self.client.get(url)
        self.assertRedirects(response, reverse('survey_list_page'), status_code=302,
                             target_status_code=200, msg_prefix='')
        self.assertEquals(Survey.objects.filter(id=survey.id).count(), 0)
        # now check if this is ignored if survey has interview
        survey = mommy.make(Survey)
        interview = mommy.make(Interview, survey=survey)
        response = self.client.get(reverse('delete_survey', args=(survey.id,)))
        self.failUnless(Survey.objects.filter(id=survey.id).count())

    def test_should_throw_error_if_deleting_with_an_open_batch(self):
        survey = Survey.objects.create(**self.form_data)
        batch = Batch.objects.create(order=1, survey=survey)
        ea = EnumerationArea.objects.create(name='EA2')
        country = LocationType.objects.create(name='country', slug='country')
        kampala = Location.objects.create(name='Kampala', type=country)
        ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name='Investigator', ea=ea, gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        batch.open_for_location(kampala)
        response = self.client.get('/surveys/%s/delete/' % survey.id)
        self.assertRedirects(response, '/surveys/', status_code=302, target_status_code=200, msg_prefix='')

    def test_survey_does_not_exist_page_reidrects(self):
        url = reverse('edit_survey_page', args=(300,))
        response = self.client.get(url)
        self.assertRedirects(response, reverse('survey_list_page'), status_code=302,
                             target_status_code=200, msg_prefix='')

    def test_sampling_criteria_page_is_accessible_with_view_batches_permission(self):
        survey = mommy.make(Survey)
        sampling_criteria_url = reverse('listing_criteria_page', args=(survey.id,))
        self.assert_restricted_permission_for(sampling_criteria_url)

    def test_post_sampling_criteria_page(self):
        self.assertEquals(Survey.objects.count(), 0)
        self.test_new_should_create_survey_on_post()
        survey = Survey.objects.first()
        sampling_criteria_url = reverse('listing_criteria_page', args=(survey.id,))
        response = self.client.get(sampling_criteria_url)
        self.assertEquals(response.status_code, 200)

    def test_create_delete_sampling_criteria(self):
        self.assertEquals(Survey.objects.count(), 0)
        self.test_new_should_create_survey_on_post()
        survey = Survey.objects.first()
        self.failUnless(survey)
        sampling_criteria_url = reverse('listing_criteria_page', args=(survey.id,))
        form_data = {'survey': survey.id, 'validation_test': 'equals',
                     'value': 1, 'listing_question': self.listing_form.questions.first().id, }
        self.assertEquals(survey.randomization_criteria.count(), 0)     # confirm nothin exists
        response = self.client.post(sampling_criteria_url, data=form_data)
        self.assertRedirects(response, sampling_criteria_url, status_code=302,
                             target_status_code=200, msg_prefix='')
        self.assertEquals(survey.randomization_criteria.count(), 1)         # confirm one criteria created
        delete_criteria_url = reverse('delete_listing_criterion', args=(survey.id, ))
        response = self.client.post(delete_criteria_url, data=form_data)    # delete criteria
        self.assertEquals(survey.randomization_criteria.count(), 0)     # confirm deleted
        self.assertRedirects(response, sampling_criteria_url, status_code=302,
                             target_status_code=200, msg_prefix='')

    def test_only_ussd_question_types_are_used_form_randomization(self):
        self.assertEquals(Survey.objects.count(), 0)
        self.test_new_should_create_survey_on_post()
        survey = Survey.objects.first()
        self.failUnless(survey)
        sampling_criteria_url = reverse('listing_criteria_page', args=(survey.id,))
        form_data = {'survey': survey.id, 'validation_test': 'equals',
                     'value': 1,
                     'listing_question': self.listing_form.questions.get(answer_type=VideoAnswer.choice_name()).id,}
        self.assertEquals(survey.randomization_criteria.count(), 0)     # confirm nothin exists
        response = self.client.post(sampling_criteria_url, data=form_data)
        self.assertEquals(survey.randomization_criteria.count(), 0)     # confirm nothin exists
        self.assertEquals(response.context['sampling_form'].is_valid(), False)

    def test_clone_survey_clones_batch_in_another_survey(self):
        self.test_new_should_create_survey_on_post()
        survey = Survey.objects.first()
        batch = mommy.make(Batch, survey=survey, description='')
        clone_url = reverse('clone_survey_page', args=(survey.id, ))
        response = self.client.get(clone_url)
        self.assertRedirects(response, reverse('survey_list_page'), status_code=302,
                             target_status_code=200, msg_prefix='')
        cloned_survey = Survey.objects.exclude(name=survey.name).first()
        self.failUnless(cloned_survey)
        self.assertFalse(cloned_survey.name == survey.name)
        self.assertIn(survey.name, cloned_survey.name)
        self.assertIn(batch.name, cloned_survey.batches.first().name)
        self.assertIn(batch.description, cloned_survey.batches.first().description)

    def test_only_super_user_can_wipe_data(self):
        user = User.objects.create_user('user1', 'user@kant.com', 'demo12')
        user.is_superuser = True
        user.is_staff = True
        user.save()
        super_user = self.assign_permission_to(user, 'can_have_super_powers')
        self.test_new_should_create_survey_on_post()
        survey = Survey.objects.first()
        batch = mommy.make(Batch, survey=survey, description='')
        wipe_off_url = reverse('wipe_survey_data', args=(survey.id, ))
        interview = mommy.make(Interview, survey=survey, question_set=batch)
        response = self.client.get(wipe_off_url)
        # confirm interview was not deleted.
        self.assertEquals(Interview.objects.filter(id=interview.id).count(), 1)
        self.client.logout()
        self.client.login(username='user1', password='demo12')
        superpowers_url = reverse('activate_super_powers_page')         # first activate superperwers
        response = self.client.get(superpowers_url)
        # views_helper.activate_super_powers()
        response = self.client.get(wipe_off_url)
        # confirm interview was not deleted.
        self.assertEquals(Interview.objects.filter(id=interview.id).count(), 0)