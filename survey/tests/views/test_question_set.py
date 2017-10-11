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