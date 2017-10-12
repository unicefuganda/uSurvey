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
        self.assign_permission_to(raj, 'can_view_aggregates')
        self.client.login(username='demo8', password='demo8')
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.district = LocationType.objects.create(
            name='District', parent=self.country, slug='district')
        self.city = LocationType.objects.create(
            name='City', parent=self.district, slug='city')
        self.village = LocationType.objects.create(
            name='village', parent=self.city, slug='village')
        self.uganda = Location.objects.create(name='Uganda', type=self.country)

        self.kampala = Location.objects.create(
            name='Kampala', parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(
            name='Kampala City', parent=self.kampala, type=self.city)
        self.ea = EnumerationArea.objects.create(name="BUBEMBE", code="11-BUBEMBE")
    
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
        self.assertRedirects(response, expected_url= reverse('batch_index_page', kwargs={"survey_id" : survey_obj.id}), msg_prefix='')
    
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


    def test_download_qset_data(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="b21", survey=survey_obj)
        qset =  QuestionSet.get(pk=batch.id)
        url = reverse('download_qset_data', kwargs={"qset_id":qset.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(response.content, ',District,City,village,EA,interviewer__name,Uploaded,Completion Date\n')

    def test_download_qset_attachment(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="b21", survey=survey_obj)
        qset =  QuestionSet.get(pk=batch.id)
        q_data = {'identifier':"dummy",
            'text' : "dummss",
            'answer_type' : "Text Answer",
            'qset_id' : qset.id
            }
        question1 = Question.objects.create(**q_data)

        
        investigator = Interviewer.objects.create(name="Investigator1",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')
        interview_obj =  Interview.objects.create(
            interviewer = investigator,
            ea = self.ea,
            survey = survey_obj,
            question_set = qset,
            )
        ans_data = {
        "question_type" : "qt1",
        "interview" : interview_obj,
        "question": question1,
        "identifier" : "identifier",
        "as_text" : "as_text",
        "as_value" : 1
        }
        ans_obj = Answer.objects.create(**ans_data)
        ans_data['value'] = 1
        url = reverse('download_qset_attachment', kwargs={"interview_id": interview_obj.id, "question_id":question1.id})
        response = self.client.get(url)
        self.assertEqual(response.content, 'TextAnswer matching query does not exist.')

        text_obj = TextAnswer.objects.create(**ans_data)
        url = reverse('download_qset_attachment', kwargs={"interview_id": interview_obj.id, "question_id":question1.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])


    def test_clone_qset_page(self):
        listing_form = ListingTemplate.objects.create(
                name="list1",
                description="list1")
        qset =  QuestionSet.get(pk=listing_form.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        url = reverse('clone_qset_page', kwargs={"qset_id" : qset.id})
        response = self.client.get(url)
        self.assertIn('Successfully cloned %s' % qset.name, response.cookies['messages'].__str__())
        self.assertRedirects(response, expected_url=reverse('listing_template_home'), msg_prefix='')
        self.assertIn(response.status_code, [200, 302])

    def test_qset_identifiers(self):
        listing_form = mommy.make(ListingTemplate)
        qset =  QuestionSet.get(pk=listing_form.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text="q7"
            )        
        url = reverse('qset_identifiers')
        url = url + "?id=%s"%question1.id
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        is_exist = False
        response_data = json.loads(response.content)
        for each in response_data:
            if each == question1.identifier:
                is_exist = True
                break
        self.assertTrue(is_exist)

        url = reverse('qset_identifiers')
        response = self.client.get(url)
        self.assertEqual(response.content, '[]')

        question2 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
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
        url = reverse('qset_identifiers')
        url = url + "?id=%s&q_id=%s"%(question1.id, question2.id)
        response = self.client.get(url)

    def test_listing_entries(self):
        listing_form = ListingTemplate.objects.create(name='l1', description='desc1')
        kwargs = {'name': 'survey9', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        
        investigator = Interviewer.objects.create(name="InvestigatorViewdata",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')

        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer = investigator,
            survey = survey_obj,
            allocation_ea = self.ea,
            status = 1

            )
        qset =  QuestionSet.get(pk=listing_form.id)
        url = reverse('listing_entries',kwargs={"qset_id":qset.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/listing_entries.html', templates)
        self.assertIn('name', response.context['placeholder'])
        self.assertIn(survey_obj, response.context['surveys'])
        self.assertEqual(qset, response.context['question_set'])
        url = url + "?q=survey9"
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        templates = [template.name for template in response.templates]
        self.assertIn('question_set/listing_entries.html', templates)
        self.assertIn('name', response.context['placeholder'])
        self.assertIn(survey_obj, response.context['surveys'])
        self.assertEqual(qset, response.context['question_set'])

    def test_listing_entries_404(self):
        url = reverse('listing_entries',kwargs={"qset_id":999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_qset_view_survey_data(self):
        listing_form = ListingTemplate.objects.create(name='l1', description='desc1')
        kwargs = {'name': 'survey10', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b1',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        
        investigator = Interviewer.objects.create(name="InvestigatorViewdata",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')
        interview_obj =  Interview.objects.create(
            interviewer = investigator,
            ea = self.ea,
            survey = survey_obj,
            question_set = qset,
            )

        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer = investigator,
            survey = survey_obj,
            allocation_ea = self.ea,
            status = 1

            )
        url = reverse('view_survey_data')
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

        url = reverse('view_survey_data')
        url = url + "?survey=%s"%survey_obj.id
        response = self.client.get(url)

        url = reverse('view_survey_data')
        url = url + "?survey=%s&question_set=%s&page=1"%(survey_obj.id, qset.id)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

        url = reverse('view_survey_data')
        url = url + "?survey=%s&question_set=%s"%(survey_obj.id, qset.id)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

    def test_qset_view_view_listing_data(self):
        listing_form = ListingTemplate.objects.create(name='l12', description='desc1')
        kwargs = {'name': 'survey11', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b1',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        
        investigator = Interviewer.objects.create(name="InvestigatorViewdata",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')
        interview_obj =  Interview.objects.create(
            interviewer = investigator,
            ea = self.ea,
            survey = survey_obj,
            question_set = qset,
            )

        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer = investigator,
            survey = survey_obj,
            allocation_ea = self.ea,
            status = 1

            )
        url = reverse('view_listing_data')
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

        url = url + "?survey=%s"%survey_obj.id
        response = self.client.get(url)

        url = reverse('view_listing_data')
        url = url + "?survey=%s&question_set=%s&page=1"%(survey_obj.id, qset.id)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

        url = reverse('view_listing_data')
        url = url + "?survey=%s&question_set=%s"%(survey_obj.id, qset.id)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

    def test_qset_view_data(self):
        listing_form = ListingTemplate.objects.create(name='l12', description='desc1')
        kwargs = {'name': 'survey12', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b1',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        
        investigator = Interviewer.objects.create(name="InvestigatorViewdata",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')
        interview_obj =  Interview.objects.create(
            interviewer = investigator,
            ea = self.ea,
            survey = survey_obj,
            question_set = qset,
            )

        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer = investigator,
            survey = survey_obj,
            allocation_ea = self.ea,
            status = 1

            )
        url = reverse('view_data_home', kwargs={"qset_id" : qset.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

        url = url + "?survey=%s"%survey_obj.id
        response = self.client.get(url)

        url = reverse('view_data_home', kwargs={"qset_id" : qset.id})
        url = url + "?survey=%s&question_set=%s&page=1"%(survey_obj.id, qset.id)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

        url = reverse('view_data_home', kwargs={"qset_id" : qset.id})
        url = url + "?survey=%s&question_set=%s"%(survey_obj.id, qset.id)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        






