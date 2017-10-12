from django.contrib.auth.models import User
from django.test.client import Client
from survey.models.locations import *
from survey.models import  QuestionModule, Interviewer, EnumerationArea, QuestionTemplate, NumericalAnswer, TextAnswer, MultiChoiceAnswer, QuestionOption, ListingTemplate
from survey.models.surveys import Survey
from survey.models.questions import Question, QuestionFlow, QuestionSet
from survey.models.batch import Batch
from survey.tests.base_test import BaseTest
from survey.forms.batch import BatchForm
from survey.forms.question_set import get_question_set_form
from survey.forms import *
from django.core.urlresolvers import reverse
import json
questionSetForm = get_question_set_form(QuestionSet)

class BatchViewsTest(BaseTest):
    def setUp(self):        
        self.client = Client()
        User.objects.create_user(
            username='useless', email='demo8@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo8', 'demo8@kant.com', 'demo8'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_batches')
        self.client.login(username='demo8', password='demo8')
        self.survey = Survey.objects.create(
            name='survey name', description='survey descrpition')
        self.batch = Batch.objects.create(
            order=1, name="Batch A", survey=self.survey)
        self.batch12 = Batch.objects.create(
            order=1, name="Batch A12", survey=self.survey)
        self.country = LocationType.objects.create(
            name="Country", slug="country")
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        district = LocationType.objects.create(
            name="District", slug="district", parent=self.country)
        self.kampala = Location.objects.create(
            name="Kampala", type=district, parent=self.uganda)
        city = LocationType.objects.create(
            name="City", slug="city", parent=district)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=city)
        self.kampala_city = Location.objects.create(
            name="Kampala City", type=city, parent=self.kampala)
        self.bukoto = Location.objects.create(
            name="Bukoto", type=city, parent=self.kampala)
        self.kamoja = Location.objects.create(
            name="kamoja", type=village, parent=self.bukoto)
        self.abim = Location.objects.create(
            name="Abim", type=district, parent=self.uganda)
        self.batch.open_for_location(self.abim)
        self.survey2 = Survey.objects.create(name='Test survey2')
        self.batch21 = Batch.objects.create(
            order=1, name="Batch A2", survey=self.survey2)
        self.ea = EnumerationArea.objects.create(name="EA2")

    def test_get_index(self):
        response = self.client.get(reverse('batch_index_page', kwargs={"survey_id" : self.survey.id}))
        self.assertEquals(response.status_code, 200)

    def test_get_batch(self):
        response = self.client.get(reverse('batch_show_page', kwargs={"survey_id":self.survey.id,"batch_id":self.batch.id}))        
        self.assertIn(response.status_code, [200,302])
        templates = [template.name for template in response.templates]
        self.assertIn('batches/show.html', templates)

    def test_get_index_should_not_show_batches_not_belonging_to_the_survey(self):
        another_batch = Batch.objects.create(order=2, name="Batch B")
        response = self.client.get(reverse('batch_index_page', kwargs={"survey_id": self.survey.id}))
        self.assertIn(response.status_code, [200,302])
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/index.html', templates)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEquals(self.survey, response.context['survey'])

    def test_open_batch_for_location(self):
        self.assertFalse(self.batch.is_open_for(self.kampala))
        response = self.client.post('/batches/' + str(self.batch.pk) + "/open_to",
                                    data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        self.batch.open_for_location(self.kampala)
        self.assertFalse(self.batch.is_open_for(self.kampala))
        json_response = json.loads(response.content)
        self.assertEqual('', json_response)

    def test_should_not_allow_open_batch_for_location_if_already_open_for_another_survey(self):
        another_survey = Survey.objects.create(name='survey name 2', description='survey descrpition 2',
                                               sample_size=10)
        another_batch = Batch.objects.create(
            order=1, name="Batch A", survey=another_survey)
        another_batch.open_for_location(self.kampala)
        self.assertFalse(another_batch.is_open_for(self.kampala))
        self.assertFalse(self.batch.is_open_for(self.kampala))
        response = self.client.post('/batches/' + str(self.batch.pk) + "/open_to",
                                    data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)

    def test_open_batch_does_not_allow_questions_to_be_assigned(self):
        another_survey = Survey.objects.create(name='survey name 2', description='survey descrpition 2',
                                               sample_size=10)
        another_batch = Batch.objects.create(
            order=1, name="Batch A", survey=another_survey)
        another_batch.open_for_location(self.kampala)
        self.assertFalse(another_batch.is_open_for(self.kampala))

    def test_close_batch_for_location(self):
        uganda123 = Location.objects.create(
            name="Uganda123", type=self.country)
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.batch.open_for_location(loc)
        response = self.client.post('/batches/' + str(self.batch.pk) + "/close_to",
                                    data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        self.assertTrue(self.batch.is_open_for(self.abim))
        json_response = json.loads(response.content)
        self.assertEqual('', json_response)

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for(
            '/surveys/%d/batches/' % self.survey.id)
        self.assert_restricted_permission_for(
            '/surveys/%d/batches/new/' % self.survey.id)
        self.assert_restricted_permission_for(
            '/surveys/%d/batches/1/' % self.survey.id)
        self.assert_restricted_permission_for('/batches/1/open_to')
        self.assert_restricted_permission_for('/batches/1/close_to')
        self.assert_restricted_permission_for(
            '/surveys/batches/%d/edit/' % (self.batch.id))
        self.assert_restricted_permission_for(
            '/surveys/%d/batches/%d/delete/' % (self.survey.id, self.batch.id))
        self.assert_login_required(
            '/surveys/%d/batches/check_name/' % (self.survey.id))

    def test_add_new_batch_should_load_new_template(self):
        response = self.client.get(reverse('new_batch_page', kwargs={'survey_id':self.survey.id}))
        self.assertIn(response.status_code, [200,302])
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/new.html', templates)

    def test_batch_form_is_in_response_request_context(self):
        response = self.client.get(reverse('new_batch_page', kwargs={'survey_id':self.survey.id}))        
        self.assertEqual(response.context['button_label'], 'Create')
        self.assertEqual(response.context['id'], 'add-question_set-form')
        self.assertEqual(response.context['title'], 'New Batch')
        self.assertEqual(response.context['button_label'], 'Create')
        self.assertEqual(response.context['cancel_url'], '/surveys/1/batches/')

    def test_post_add_new_batch(self):
        data = {'name': 'Batch1', 'description': 'description'}
        response = self.client.post(
            '/surveys/%d/batches/new/' % self.survey.id, data=data)
        self.assertEqual(len(Batch.objects.filter(
            survey__id=self.survey.id, **data)), 0)

    def test_post_add_new_batch_should_add_batch_to_the_survey(self):
        batch = Batch.objects.create(
            order=1, name="Some Batch", description="some description", survey=self.survey)
        form_data = {'name': 'Some Batch', 'description': 'some description'}
        response = self.client.post(
            '/surveys/%d/batches/new/' % self.survey.id, data=form_data)

        batch = Batch.objects.get(**form_data)
        self.assertEqual(self.survey, batch.survey)

    def test_edit_batch_should_load_new_template(self):
        batch = Batch.objects.create(
            survey=self.survey, name="batch a", description="batch a description")
        response = self.client.get(reverse('edit_batch_page',kwargs={'batch_id':self.batch.id}))
        self.assertIn(response.status_code, [200,302])
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/new.html', templates)

    def test_edit_batch_page_gets_batch_form_instance(self):
        batch = Batch.objects.create(
            survey=self.survey, name="batch a", description="batch a description")
        response = self.client.get(reverse('edit_batch_page',kwargs={'batch_id':self.batch.id}))        
        self.assertEqual(response.context['id'], 'edit-question-set-form')
        self.assertEqual(response.context['placeholder'], 'name, description')
        self.assertEqual(response.context['listing_model'], ListingTemplate)
        self.assertEqual(response.context['model'], Batch)

    def test_delete_batch(self):
        self.batch.close_for_location(self.abim)
        self.assertFalse(self.batch.is_open())
        response = self.client.get(reverse('delete_batch', kwargs={'survey_id':self.survey.id, 'batch_id':self.batch.id}))
        self.assertIn(response.status_code, [200,302])
        recovered_batch = Batch.objects.filter(id=self.batch.id)
        self.assertRedirects(response, reverse('batch_index_page', kwargs={"survey_id" : self.survey.id}), msg_prefix='')
        self.failIf(recovered_batch)

    def test_should_tell_if_name_is_already_taken(self):
        batch = Batch.objects.create(
            survey=self.survey, name="batch a", description="batch a description")
        response = self.client.get(
            '/surveys/%d/batches/check_name/?name=%s' % (self.survey.id, batch.name))
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)
        response = self.client.get(
            '/surveys/%d/batches/check_name/?name=%s' % (self.survey.id, 'some other name that does not exist'))
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)
    
    def test_survey_id_is_None(self):
        batch = Batch.objects.create(
            survey=self.survey, name="batch a", description="batch a description")
        response = self.client.get(reverse('survey_batches_page', kwargs={"survey_id" : self.survey.id}))
        self.failUnlessEqual(response.status_code, 200)