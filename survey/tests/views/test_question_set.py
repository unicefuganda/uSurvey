from django.contrib.auth.models import User
from django.test import Client
from survey.forms.question_module_form import QuestionModuleForm
# from survey.forms.question_set import QuestionSetForm, BatchForm
from model_mommy import mommy
from survey.forms import *
from survey.models import *
from survey.models.batch import *
from survey.tests.base_test import BaseTest
from survey.forms.batch import BatchForm
from survey.forms.question_set import get_question_set_form
from survey.views.question_set import QuestionSetView
import json

class QuestionSetViewTest(BaseTest):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username='useless', email='demo8@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('demo8', 'demo8@kant.com', 'demo8'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_investigators')
        self.client.login(username='demo8', password='demo8')
    
    def test_index(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="Batch A1", survey=survey_obj)
        response = self.client.get(reverse('batch_index_page', kwargs={"survey_id" : survey_obj.id}))
        self.assertIn(response.status_code, [200, 302])
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/index.html', templates)
        self.assertIn('name, description', response.context['placeholder'])
        self.assertEqual(Batch, response.context['model'])
        self.assertEqual(Batch.__name__, response.context['model_name'])
        self.assertIn(batch, response.context['question_sets'])
        self.assertEqual(survey_obj, response.context['survey'])

    def test_delete_should_delete_the_question(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="Batch ABC", survey=survey_obj)
        qset = QuestionSet.get(id=batch.id)
        response = self.client.get(reverse('delete_qset', kwargs={"question_id":qset.id, "batch_id":survey_obj.id}))
        self.assertIn('Question Set Deleted Successfully', response.cookies['messages'].__str__())
        self.assertRedirects(response, reverse('batch_index_page', kwargs={"survey_id" : survey_obj.id}), msg_prefix='')
    
    def test_delete_should_throws_404(self):
        response = self.client.get(reverse('delete_qset', kwargs={"question_id":999, "batch_id":999}))
        self.assertEqual(response.status_code, 404)

    def test_search_questionset(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="bsearch", survey=survey_obj)
        url = reverse('batch_index_page', kwargs={"survey_id" : survey_obj.id})
        url = url+"?q=bsearch"
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/index.html', templates)
        self.assertIn('name, description', response.context['placeholder'])
        self.assertEqual(Batch, response.context['model'])
        self.assertEqual(Batch.__name__, response.context['model_name'])
        self.assertIn(batch, response.context['question_sets'])
        self.assertEqual(survey_obj, response.context['survey'])

    def test_question_options_by_question(self):
        listing_form = mommy.make(ListingTemplate)
        qset =  QuestionSet.get(pk=listing_form.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text="q1"
            )        
        url = reverse('question_options')
        url = url + "?ques_id=%s"%question1.id
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(response.content, '{"1": "q1"}')


    def test_question_options_by_qset(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="bsearch", survey=survey_obj)
        qset =  QuestionSet.get(pk=batch.id)
        question1 = mommy.make(Question, qset=qset, answer_type=TextAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=3,
            text="q3"
            )

        question2 = mommy.make(Question, qset=qset, answer_type=TextAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=4,
            text="q4"
            )
        QuestionFlow.objects.create(
            name = 'a1',
            desc = 'descq',
            question = question2,
            question_type = TextAnswer.choice_name(),
            next_question = question1,
            next_question_type = TextAnswer.choice_name()
            )
        QuestionLoop.objects.create(
            loop_starter = question2,
            loop_ender = question1
            )
        url = reverse('question_options')
        url = url + "?id=%s"%qset.id
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(response.content,'{}')

    def test_question_validators(self):
        listing_form = mommy.make(ListingTemplate)
        qset =  QuestionSet.get(pk=listing_form.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text="q5"
            )        
        url = reverse('question_validators')
        url = url + "?ques_id=%s"%question1.id
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(response.content, '["equals", "between", "less_than", "greater_than"]')

        url = reverse('question_validators')
        url = url + "?id=%s"%qset.id
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(response.content, '{}')


    def test_list_questions(self):
        listing_form = mommy.make(ListingTemplate)
        qset =  QuestionSet.get(pk=listing_form.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text="q6"
            )        
        url = reverse('list_questions')
        url = url + "?id=%s"%qset.id
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(response.content, '[]')

        url = reverse('list_questions')
        response = self.client.get(url)
        response_data = json.loads(response.content)
        is_exist = False
        for each in response_data:
            if each['id'] == question1.id:
                is_exist = True
                break
        self.assertTrue(is_exist)


    def test_list_qsets(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="b2", survey=survey_obj)
        qset =  QuestionSet.get(pk=batch.id)
        url = reverse('view_qsets')
        url = url + "?survey_id=%s"%survey_obj.id
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        response_data = json.loads(response.content)
        is_exist = False
        for each in response_data:
            if each['id'] == batch.id:
                is_exist = True
                break
        self.assertTrue(is_exist)
    
        url = reverse('view_qsets')
        response = self.client.get(url)
        is_exist = False
        response_data = json.loads(response.content)
        for each in response_data:
            if each['id'] == batch.id:
                is_exist = True
                break
        self.assertTrue(is_exist)


 