import json
from model_mommy import mommy
from django.contrib.auth.models import User
from model_mommy import mommy
from django.test.client import Client
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import *
from survey.utils.query_helper import get_filterset
from survey.tests.base_test import BaseTest
from survey.forms.question import get_question_form
from survey.tests.models.survey_base_test import SurveyBaseTest
from survey.views.set_questions import remove_loop


class SetQuestionViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.listing_data = {'name': 'test-listing', 'access_channels': [ODKAccess.choice_name(), ], }
        self.questions_data = []
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest", constraint_message="message")
        # create a inline flows for this listing
        for answer_class in [NumericalAnswer, TextAnswer, DateAnswer, MultiChoiceAnswer]:
            self.questions_data.append({'text': 'text: %s' % answer_class.choice_name(),
                                        'answer_type': answer_class.choice_name(),
                                        'identifier': 'id: %s' % answer_class.choice_name()})
        self.questions_data[-1]['options'] = ['Yes', 'No']
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client.login(username='demo12', password='demo12')
        self.listing_form_data = {
            'name': 'test listing1',
            'description': 'listing description demo6'
        }
        self.qset_form_data = {
            'name': 'test listing1 q1',
            'description': 'listing description demo6',
        }
        self.sub_data={
            'identifier':"dummy",
            'response_validation':self.rsp,
            'text' : "dummss",
            'answer_type' : "Text Answer"
        }
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

    def test_add_subquestion(self):
        l_qset = ListingTemplate.objects.create(**self.listing_form_data)
        qset = QuestionSet.objects.get(pk=l_qset.id)
        q_obj = Question.objects.create(identifier='identifiersss', text="This is a questiod",
                                        answer_type='Numerical Answer', qset_id=l_qset.id,
                                        response_validation_id=self.rsp.id)
        self.sub_data['parent_question'] = q_obj
        response = self.client.post(reverse('add_qset_subquestion_page', kwargs={"batch_id" : l_qset.id}),
                                    self.sub_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn(response.status_code, [200, 302])
        templates = [template.name for template in response.templates]
        self.assertIn('set_questions/_add_question.html', templates)

    def test_view_questions_list(self):
        list_1 = ListingTemplate.objects.create(**self.listing_form_data)
        response = self.client.get(reverse('listing_template_home'))
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id':list_1.id}))
        self.assertEqual(200, response.status_code)

    def test_add_question(self):
        list_1 = ListingTemplate.objects.create(name="List A2")
        batch = QuestionSet.get(pk=list_1.id)
        qset1 = QuestionSet.objects.create(name="dummy", description="bla bla")
        response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id': list_1.id}))
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('set_questions/index.html', templates)
        self.assertNotIn('Add Question', response.context['title'])
        self.assertNotIn(reverse('qset_questions_page', kwargs={'qset_id':list_1.id}), response.context['action'])

    def test_questionset_doesnotexist(self):
        response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id': 99999}))
        self.assertEqual(404, response.status_code)

    def test_question_filters(self):
        search_fields = ['identifier', 'text', ]
        list_1 = ListingTemplate.objects.create(name="ListA3")
        batch = QuestionSet.get(pk=list_1.id)
        q1 = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=list_1.id, response_validation_id=self.rsp.id)
        response = self.client.get(reverse('qset_questions_page', kwargs={'qset_id':list_1.id}))
        q = 'q2'
        qset_questions = batch.questions.all()
        filter_result = get_filterset(qset_questions, q, search_fields)
        response = self.client.get("%s?q=ListA3"%(reverse('qset_questions_page', kwargs={'qset_id':list_1.id})))
        self.assertEqual(200, response.status_code)
        response = self.client.get("%s?q=ListA3&question_types=Numerical Answer"%(reverse('qset_questions_page',
                                                                                          kwargs={'qset_id':list_1.id})))
        self.assertEqual(200, response.status_code)

    def test_new_subquestion(self):
        survey_obj = Survey.objects.create(
            name='survey name12baaf', description='survey descrpition')
        batch_obj = Batch.objects.create(
            order=1, name="Baaatchff Abcrrr", survey=survey_obj)
        list_1 = ListingTemplate.objects.create(name="List A9")

        qset = QuestionSet.get(pk=batch_obj.id)
        response = self.client.get(reverse('add_qset_subquestion_page', kwargs={"batch_id" : batch_obj.id}))
        qset = QuestionSet.get(pk=list_1.id)
        response = self.client.get(reverse('add_qset_subquestion_page', kwargs={"batch_id" : qset.id}))
        self.assertIn(response.status_code, [200, 302])
        # templates = [ template.name for template in response.templates ]
        # self.assertIn('set_questions/_add_question.html', templates)
        module_obj = QuestionModule.objects.create(name='test')
        qset_obj = QuestionSet.objects.create(name="Females")
        rsp_obj = ResponseValidation.objects.create(validation_test="validationtest",constraint_message="message")
        data = {"qset_id" :qset_obj.id,  "identifier" : '', "text": "hello","answer_type":'',
                "response_validation_id": self.rsp.id }
        response = self.client.post(reverse('add_qset_subquestion_page', kwargs={"batch_id" : qset.id}),data=data)
        self.assertIn(response.status_code, [200, 302])
        self.client.post(reverse('add_qset_subquestion_page', kwargs={"batch_id" : batch_obj.id}),data={})
        self.assertIn(response.status_code, [200, 302])


    def test_get_sub_questions_for_question(self):
        list_1 = ListingTemplate.objects.create(name="List A2")
        qset = QuestionSet.get(pk=list_1.id)
        q_obj = Question.objects.create(identifier='123.1', text="This is a question123.1", answer_type='Numerical Answer',
                                                  qset_id=qset.id, response_validation_id=self.rsp.id)
        response = self.client.get(reverse('questions_subquestion_json_page', kwargs={"question_id" : q_obj.id}))
        self.assertIn(response.status_code, [200, 302])

    def test_add_listing(self):
        create_qset_url = reverse('new_%s_page' % ListingTemplate.resolve_tag())
        response = self.client.post(create_qset_url, data=self.listing_data)
        self.assertEquals(ListingTemplate.objects.count(), 1)
        self.assertEquals(ListingTemplate.objects.first().name, self.listing_data['name'])

    def text_add_question_fails_if_id_has_space(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        data = self.questions_data[0]
        response = self.client.post(create_sq_url, data=data)
        self.assertIn(Question.objects.count(), 0)
        self.assertIn('questionform' in response.context)
        self.assertEquals(response.context['questionform'].is_valid(), False)

    def test_add_question_to_listing(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        for data in self.questions_data:
            data['identifier'] = data['identifier'].replace(':', '').replace(' ', '')
            data['qset'] = listing.pk
            response = self.client.post(create_sq_url, data=data)
            question = Question.objects.order_by('created').last()
            self.assertEquals(question.text, data['text'])
            self.assertEquals(question.identifier, data['identifier'])
            self.assertEquals(question.answer_type, data['answer_type'])

    def test_insert_question_to_listing(self):
        self.test_add_question_to_listing()
        self.assertTrue(Question.objects.count() > 2)
        inlines = QuestionSet.objects.first().questions_inline()
        question = inlines[1]
        insert_sq_url = reverse('insert_qset_question_page', args=(question.pk, ))
        data = {'text': 'text: %s' % TextAnswer.choice_name(),
                'answer_type': TextAnswer.choice_name(),
                'identifier': 'test_insert_id',
                'qset': question.qset.pk}
        response = self.client.post(insert_sq_url, data=data)
        self.assertTrue(response.status_code, 302)
        inlines = question.qset.questions_inline()
        self.assertEquals(data['identifier'], inlines[2].identifier)
        self.assertEquals(data['text'], inlines[2].text)
        self.assertEquals(data['answer_type'], inlines[2].answer_type)

    def test_add_to_library_flag_for_add_question_to_listing(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        data = self.questions_data[0]
        data['add_to_lib_button'] = 1
        data['qset'] = listing.pk
        data['identifier'] = data['identifier'].replace(':', '').replace(' ', '')
        response = self.client.post(create_sq_url, data=data)
        question = Question.objects.order_by('created').last()
        self.assertEquals(question.text, data['text'])
        self.assertEquals(question.identifier, data['identifier'])
        self.assertEquals(question.answer_type, data['answer_type'])
        question_template = QuestionTemplate.objects.first()
        self.assertEquals(question_template.text, data['text'])
        self.assertEquals(question_template.identifier, data['identifier'])
        self.assertEquals(question_template.answer_type, data['answer_type'])

    def test_add_more_button_returns_to_same_page(self):
        self.test_add_listing()
        listing = ListingTemplate.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(listing.pk, ))
        data = self.questions_data[0]
        data['add_more_button'] = 1
        data['qset'] = listing.pk
        data['identifier'] = data['identifier'].replace(':', '').replace(' ', '')
        response = self.client.post(create_sq_url, data=data)
        question = Question.objects.order_by('created').last()
        self.assertEquals(question.text, data['text'])
        self.assertEquals(question.identifier, data['identifier'])
        self.assertEquals(question.answer_type, data['answer_type'])
        question_template = QuestionTemplate.objects.first()
        self.assertIn(create_sq_url, response.url)

    def test_restricted_permissions(self):
        self.assert_restricted_permission_for('/qset/questions/1/new/')
        self.assert_restricted_permission_for('/qsets/2/questions/')
        self.assert_restricted_permission_for('/set_questions/1/edit/')
        self.assert_restricted_permission_for('/qset/questions/1/insert/')

    def test_get_sub_questions_for_question(self):
        list_1 = ListingTemplate.objects.create(name="naList b2")
        qset = QuestionSet.get(pk=list_1.id)
        q_obj = Question.objects.create(identifier='id_1', text="This is a question123.5", answer_type='Numerical Answer',
                                                  qset_id=qset.id, response_validation_id=self.rsp.id)
        response = self.client.get(reverse('questions_subquestion_json_page', kwargs={"question_id" : q_obj.id}))
        self.assertIn(response.status_code,[200,302])

    def test_delete(self):
        list_1 = ListingTemplate.objects.create(name="List b3fgfg")
        survey_obj = Survey.objects.create(
            name='survey name2dddd', description='survey descrpition2')
        batch_obj = Batch.objects.create(
            order=1, name="Batchdddd A2", survey=survey_obj)
        qset = QuestionSet.get(pk=batch_obj.id)
        q_obj = Question.objects.create(identifier='id_2', text="This is a question123.6",
                                        answer_type='Numerical Answer', qset_id=qset.id,
                                        response_validation_id=self.rsp.id)
        response = self.client.get(reverse('delete_question_page', kwargs={"question_id" : q_obj.id}))
        self.assertIn(response.status_code, [200, 302])

    def test_edit_subquestion(self):
        survey_obj = Survey.objects.create(
            name='survey name2', description='survey descrpition2')
        batch_obj = Batch.objects.create(
            order=1, name="Batch A2", survey=survey_obj)
        list_1 = ListingTemplate.objects.create(name="List b5")
        qset = QuestionSet.get(pk=list_1.id)
        q_obj = Question.objects.create(identifier='id_5', text="This is a question123.9",
                                        answer_type='Numerical Answer', qset_id=qset.id,
                                        response_validation_id=self.rsp.id)
        response = self.client.get(reverse('edit_batch_subquestion_page',
                                           kwargs={"batch_id" : batch_obj.id,"question_id": q_obj.id}))
        self.assertIn(response.status_code, [200, 302])

    def test_get_questions_for_batch(self):
        survey_obj = Survey.objects.create(
            name='survey name1', description='survey descrpition1')
        batch_obj = Batch.objects.create(
            order=1, name="Batch A1", survey=survey_obj)
        # list_1 = ListingTemplate.objects.create(name="List A10")
        qset = QuestionSet.get(id=batch_obj.id)
        q_obj = Question.objects.create(identifier='id_4', text="This is a question123.8",
                                        answer_type='Numerical Answer', qset_id=qset.id,
                                        response_validation_id=self.rsp.id)
        response = self.client.get(reverse('batch_questions_json_page',
                                           kwargs={"batch_id": batch_obj.id, "question_id": q_obj.id}))
        self.assertIn(response.status_code, [200, 302])

    def test_remove(self):
        qset = ListingTemplate.objects.create(name="List b4")
        q_obj = Question.objects.create(identifier='id_3', text="This is a question123.7",
                                        answer_type='Numerical Answer',
                                        qset=qset, response_validation_id=self.rsp.id)
        response = self.client.get(reverse('remove_qset_question_page', kwargs={"question_id" : q_obj.id}))
        self.assertFalse(Question.objects.filter(id=q_obj.id).exists())
        self.assertIn(response.status_code, [200, 302])

    def test_export_questions_in_qset(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="b21abc", survey=survey_obj)
        qset =  QuestionSet.get(pk=batch.id)
        url = reverse('export_questions_in_qset', kwargs={"qset_id":qset.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

    def test_remove_question_loop_page(self):
        listing_form = ListingTemplate.objects.create(name='l121a', description='desc1')
        kwargs = {'name': 'survey121a', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b1aaaa',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        investigator = Interviewer.objects.create(name="InvestigatorViewdata",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0, date_of_birth='1987-01-01')
        interview_obj= Interview.objects.create(
            interviewer= investigator,
            ea= self.ea,
            survey= survey_obj,
            question_set= qset,
            )
        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer= investigator,
            survey= survey_obj,
            allocation_ea= self.ea,
            status= SurveyAllocation.LISTING
            )

        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text="q7"
            )
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
        loop_obj = QuestionLoop.objects.create(
            loop_starter = question2,
            loop_ender = question1
            )
        url = reverse('remove_question_loop_page', kwargs={"loop_id":loop_obj.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertRedirects(response, expected_url=reverse('qset_questions_page',
                                                            kwargs={"qset_id" : qset.id}), msg_prefix='')

    def test_update_question_order_page_on_empty(self):
        listing_form = ListingTemplate.objects.create(name='l12', description='desc1')
        kwargs = {'name': 'survey11', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b1',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)

        url = reverse('qset_update_question_order_page', kwargs={"qset_id" : qset.id})
        response = self.client.post(url,data={"order_information": []})
        self.assertIn(response.status_code, [200, 302])
        self.assertIn("No questions orders were updated.", response.cookies['messages'].__str__())
        self.assertRedirects(response, expected_url= reverse('qset_questions_page', kwargs={"qset_id" : qset.id}),
                             msg_prefix='')

    def test_update_question_order_page(self):
        listing_form = ListingTemplate.objects.create(name='l12xa', description='desc1')
        kwargs = {'name': 'survey11uz', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b190000',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)

        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text="q7"
            )
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
        loop_obj = QuestionLoop.objects.create(
            loop_starter = question2,
            loop_ender = question1
            )
        url = reverse('qset_update_question_order_page', kwargs={"qset_id" : qset.id})
        response = self.client.post(url,data={"order_information": [batch_obj.id]})
        self.assertIn(response.status_code, [200, 302])
        self.assertRedirects(response, expected_url= reverse('qset_questions_page',
                                                             kwargs={"qset_id" : qset.id}), msg_prefix='')

    def test_qset_assign_questions_page_assign(self):
        listing_form = ListingTemplate.objects.create(name='l12xa11', description='desc1')
        kwargs = {'name': 'survey11uz11ww', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='baaa1900010w',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)

        question1 = mommy.make(Question, qset=qset, answer_type=MultiChoiceAnswer.choice_name())
        investigator = Interviewer.objects.create(name="Investigator1",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0, date_of_birth='1987-01-01')
        interview_obj= Interview.objects.create(interviewer=investigator, ea=self.ea,
                                                survey=survey_obj, question_set=qset,
                                                )
        option1_text = 'q7'
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text=option1_text
            )
        ans_args = (interview_obj, question1, option1_text)
        answer_class = Answer.get_class(question1.answer_type)
        ans_obj = answer_class.create(*ans_args)
        question2 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=4,
            text="q4"
            )
        QuestionFlow.objects.create(
            name= 'a1',
            desc= 'descq',
            question= question2,
            question_type= TextAnswer.choice_name(),
            next_question= question1,
            next_question_type= TextAnswer.choice_name()
            )
        loop_obj= QuestionLoop.objects.create(
            loop_starter= question2,
            loop_ender= question1
            )
        url = reverse('qset_assign_questions_page', kwargs={"qset_id": qset.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertRedirects(response, expected_url= reverse('qset_questions_page', kwargs={"qset_id": qset.id}),
                             msg_prefix='')
        batch_obj = Batch.objects.create(name='b190aa0010w11',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        url = reverse('qset_assign_questions_page', kwargs={"qset_id": qset.id})
        response = self.client.post(url, data={"identifier": "identifier_demo"})
        self.assertRedirects(response, expected_url= reverse('qset_questions_page',
                                                             kwargs={"qset_id": qset.id}), msg_prefix='')
        # self.assertIn("Questions successfully assigned to Batch: %s.\\" % batch_obj.name,
        #               response.cookies['messages'].__str__())
        self.assertRedirects(response, expected_url= reverse('qset_questions_page',
                                                             kwargs={"qset_id": qset.id}), msg_prefix='')



    def test_export_questions_in_qset(self):
        survey_obj = mommy.make(Survey)
        batch = Batch.objects.create(order=1, name="b21abc", survey=survey_obj)
        qset =  QuestionSet.get(pk=batch.id)
        url = reverse('export_questions_in_qset', kwargs={"qset_id":qset.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

    def test_remove_question_loop_page(self):
        listing_form = ListingTemplate.objects.create(name='l121a', description='desc1')
        kwargs = {'name': 'survey121a', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b1aaaa',description='d1', survey=survey_obj)
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

        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text="q7"
            ) 
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
        loop_obj = QuestionLoop.objects.create(
            loop_starter = question2,
            loop_ender = question1
            )
        url = reverse('remove_question_loop_page', kwargs={"loop_id":loop_obj.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertRedirects(response, expected_url= reverse('qset_questions_page', kwargs={"qset_id" : qset.id}), msg_prefix='')

    def test_update_question_order_page_on_empty(self):
        listing_form = ListingTemplate.objects.create(name='l12', description='desc1')
        kwargs = {'name': 'survey11', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b1',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        
        url = reverse('qset_update_question_order_page', kwargs={"qset_id" : qset.id})
        response = self.client.post(url,data={"order_information": []})
        self.assertIn(response.status_code, [200, 302])
        self.assertIn("No questions orders were updated.", response.cookies['messages'].__str__())
        self.assertRedirects(response, expected_url= reverse('qset_questions_page', kwargs={"qset_id" : qset.id}), msg_prefix='')

    def test_update_question_order_page(self):
        listing_form = ListingTemplate.objects.create(name='l12xa', description='desc1')
        kwargs = {'name': 'survey11uz', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b190000',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        QuestionOption.objects.create(
            question=question1,
            order=1,
            text="q71"
            ) 
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
        loop_obj = QuestionLoop.objects.create(
            loop_starter = question2,
            loop_ender = question1
            )
        url = reverse('qset_update_question_order_page', kwargs={"qset_id" : qset.id})
        response = self.client.post(url,data={"order_information": [batch_obj.id]})
        self.assertIn(response.status_code, [200, 302])
        self.assertRedirects(response, expected_url = reverse('qset_questions_page',
                                                             kwargs={"qset_id" : qset.id}), msg_prefix='')

    def test_add_question_logic_page(self):
        listing_form = ListingTemplate.objects.create(name='lz1', description='desc1')
        kwargs = {'name': 'sz1', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='bz1',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        question2 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        url = reverse('add_question_logic_page', kwargs = {"qset_id" : qset.id, "question_id": question1.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        templates = [ template.name for template in response.templates ]
        self.assertIn('set_questions/logic.html', templates)
        self.assertEquals(response.context['class'], 'question-form')
        self.assertEquals(response.context['batch'], batch_obj)
        self.assertEquals(response.context['batch_id'], "%s"%batch_obj.id)
        logic_form = {
        "condition" : "equals",
        "attribute" : "value",
        "value" :3,
        "min_value" :1,
        "max_value" : 3,
        "action" : "END_INTERVIEW",
        "next_question" : question2.id
        }
        response = self.client.post(url, data=logic_form)

    def test_remove_question_loop_page(self):
        listing_form = ListingTemplate.objects.create(name='lz2', description='desc1')
        kwargs = {'name': 'sz2', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='bz2',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        question2 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        ql_obj = QuestionLoop.objects.create(
            loop_starter = question1,
            repeat_logic = '',
            loop_ender = question2,
            loop_prompt = 'loop_prompt1'
            )
        url = reverse('remove_question_loop_page', kwargs = {"loop_id" : ql_obj.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

        url = reverse('remove_question_loop_page', kwargs = {"loop_id" : 9999})
        response = self.client.get(url)
        self.assertIn(response.status_code, [404])


    def test_delete_logic(self):
        listing_form = ListingTemplate.objects.create(name='lz3', description='desc1')
        kwargs = {'name': 'sz3', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='bz3',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        question2 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())

        qf_obj =  QuestionFlow.objects.create(
            name = 'a1',
            desc = 'descq',
            question = question1,
            question_type = TextAnswer.choice_name(),
            next_question = question2,
            next_question_type = TextAnswer.choice_name()
            )
        
        url = reverse('delete_qset_question_logic_page', kwargs = {"flow_id" : qf_obj.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

        url = reverse('delete_qset_question_logic_page', kwargs = {"flow_id" : 9999})
        response = self.client.get(url)
        self.assertIn(response.status_code, [404])

    def test_qset_edit_question_page(self):
        listing_form = ListingTemplate.objects.create(name='lz3', description='desc1')
        kwargs = {'name': 'sz3', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='bz3',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        question2 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        url = reverse('qset_edit_question_page', kwargs={"question_id":question1.id})
        response = self.client.get(url)
        templates = [ template.name for template in response.templates ]
        self.assertIn('set_questions/new.html', templates)

    def test_json_create_response_validation(self):
        rsp_form = {
            "min" :2,
            "max" :3,
            "value":3,
            "validation_test" : 'equals'
        }
        url = reverse('json_create_response_validation')
        response = self.client.post(url, data=rsp_form)
        self.assertIn(response.status_code, [200, 302])
        expcted_ouput = {"success": True, "created": {"text": "equals: 3", "id": 2}}
        self.assertEquals(json.loads(response.content), expcted_ouput)
        rsp_form = {
            "min":'fd',
            "max":'esdfds',
            "value":3,
            "validation_test": '0'
        }

        url = reverse('json_create_response_validation')
        expcted_ouput= {"success": False, "error": {"__all__": ["unsupported validator defined on test question"], "validation_test": ["Select a valid choice. 0 is not one of the available choices."]}}
        response = self.client.post(url, data=rsp_form)
        self.assertIn(response.status_code, [200, 302])
        self.assertEquals(json.loads(response.content), expcted_ouput)

        url = reverse('json_create_response_validation')
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        expcted_ouput = {}
        self.assertEquals(json.loads(response.content), expcted_ouput)

    def _create_ussd_non_group_questions(self, qset=None):
        if qset is None:
            qset = self.qset
        # numeric answer
        data = {
            'answer_type': NumericalAnswer.choice_name(),
            'text': 'num text',
            'identifier': 'num1_identifier',
            'qset': qset.id
        }
        question = self._save_question(qset, data)
        qset.refresh_from_db()  # qset is updated by question (start_question attribute is updated)
        # since it's the first question saved it must reflect as first question of the question set
        self.assertEquals(qset.start_question.id, question.id)
        # text answer
        data = {
            'answer_type': TextAnswer.choice_name(),
            'text': 'texts text',
            'identifier': 'text1_identifier_',
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Multichoice questions
        data = {
            'answer_type': MultiChoiceAnswer.choice_name(),
            'text': 'multichoice answer text',
            'identifier': 'multi1_choice_identifier_',
            'qset': qset.id,
            'options': ['Y', 'N']
        }
        self._save_question(qset, data)
        # Auto questions
        data = {
            'answer_type': AutoResponse.choice_name(),
            'text': 'auto answer text',
            'identifier': 'auto1_identifier_',
            'qset': qset.id,
        }
        self._save_question(qset, data)
        qset.refresh_from_db()

    def _save_question(self, qset, data):
        current_count = Question.objects.count()
        question_class = BatchQuestion
        if qset.__class__ == Question:
            question_class = Question
        QuestionForm = get_question_form(question_class)
        question_form = QuestionForm(qset, data=data)
        self.assertTrue(question_form.is_valid())
        question = question_form.save()
        self.assertEquals(Question.objects.count(), current_count + 1)
        return question

    def test_listing_update_question_order(self):
        import random
        qset = mommy.make(ListingTemplate)
        self.qset_channels = mommy.make(QuestionSetChannel, qset=qset, channel=ODKAccess.choice_name())
        self._create_ussd_non_group_questions(qset)
        questions = list(Question.objects.all())
        flow_questions = list(qset.flow_questions)
        self.assertTrue(flow_questions[0].id, questions[0].id)
        self.assertTrue(flow_questions[-1].id, questions[-1].id)
        random.shuffle(questions)
        data = {'order_information': ['%s-%s' % (idx, question.id) for idx, question in enumerate(questions)]}
        url = reverse('qset_update_question_order_page', args=(qset.id, ))
        response = self.client.post(url, data=data)
        self.assertTrue(response.status_code in [200, 302])
        # if successful first flow should be last
        new_flow_questions = list(qset.flow_questions)
        for idx, question in enumerate(new_flow_questions):
            self.assertTrue(question.id, questions[idx].id)
        # lets shuffle and try again
        random.shuffle(questions)
        data = {'order_information': ['%s-%s' % (idx, question.id) for idx, question in enumerate(questions)]}
        url = reverse('qset_update_question_order_page', args=(qset.id,))
        response = self.client.post(url, data=data)
        self.assertTrue(response.status_code in [200, 302])
        # if successful first flow should be last
        new_flow_questions = list(qset.flow_questions)
        for idx, question in enumerate(new_flow_questions):
            self.assertTrue(question.id, questions[idx].id)

    def test_batch_update_question_order(self):
        import random
        qset = mommy.make(Batch, survey=mommy.make(Survey))
        self.qset_channels = mommy.make(QuestionSetChannel, qset=qset, channel=ODKAccess.choice_name())
        self._create_ussd_non_group_questions(qset)
        questions = list(Question.objects.all())
        flow_questions = list(qset.flow_questions)
        self.assertTrue(flow_questions[0].id, questions[0].id)
        self.assertTrue(flow_questions[-1].id, questions[-1].id)
        random.shuffle(questions)
        data = {'order_information': ['%s-%s' % (idx, question.id) for idx, question in enumerate(questions)]}
        url = reverse('qset_update_question_order_page', args=(qset.id, ))
        response = self.client.post(url, data=data)
        self.assertTrue(response.status_code in [200, 302])
        # if successful first flow should be last
        new_flow_questions = list(qset.flow_questions)
        for idx, question in enumerate(new_flow_questions):
            self.assertTrue(question.id, questions[idx].id)
        # lets shuffle and try again
        random.shuffle(questions)
        data = {'order_information': ['%s-%s' % (idx, question.id) for idx, question in enumerate(questions)]}
        url = reverse('qset_update_question_order_page', args=(qset.id,))
        response = self.client.post(url, data=data)
        self.assertTrue(response.status_code in [200, 302])
        # if successful first flow should be last
        new_flow_questions = list(qset.flow_questions)
        for idx, question in enumerate(new_flow_questions):
            self.assertTrue(question.id, questions[idx].id)

    def test_create_sub_question(self):
        qset = mommy.make(ListingTemplate)
        question = mommy.make(Question, qset=qset)
        qset.start_question = question
        qset.save()
        mommy.make(QuestionSetChannel, qset=qset, channel=ODKAccess.choice_name())
        url = reverse('add_batch_subquestion_page', args=(qset.id, ))
        data = {
            'answer_type': TextAnswer.choice_name(),
            'text': 'sub question',
            'identifier': 'text1_identifier_subqestion',
            'qset': qset.id
        }
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest', data=data)
        self.assertEquals(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(response_data['text'], data['text'])
        sub_question = qset.questions.last()
        # now edit subquestion with previous question
        url = reverse('edit_batch_subquestion_page', args=(qset.id, sub_question.id))
        new_data = {
            'answer_type': TextAnswer.choice_name(),
            'text': 'Edited sub question',
            'identifier': 'text1_identifier_subqestion',
            'qset': qset.id
        }
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest', data=new_data)
        self.assertEquals(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(response_data['text'], new_data['text'])
        self.assertEquals(Question.objects.filter(qset=qset, identifier='text1_identifier_subqestion').count(), 1)


class SetQuestionsViewExtra(SurveyBaseTest):

    def setUp(self):
        super(SetQuestionsViewExtra, self).setUp()
        self.user = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client.login(username='demo12', password='demo12')

    def test_get_previous_questions_for_question(self):
        self._create_ussd_non_group_questions()
        questions = Question.objects.order_by('created')
        self.assertEquals(questions.count(), 4)
        question = questions[2]
        url = reverse('prev_inline_questions_json_page', args=(question.id, ))
        response = self.client.get(url)
        response_data = json.loads(response.content)
        for entry in response_data:
            self.assertTrue(questions.exclude(id__in=[questions[2].id,
                                                      questions[3].id]).filter(id=entry["id"]).exists())

    def test_remove_loop(self):
        self._create_ussd_group_questions()
        loop = mommy.make(QuestionLoop, loop_starter=Question.objects.first(),
                          loop_ender=Question.objects.last())
        self.assertTrue(QuestionLoop.objects.exists())
        url = reverse('remove_question_loop_page', args=(loop.id, ))
        response = self.client.get(url)
        self.assertFalse(QuestionLoop.objects.exists())

    def test_remove_loop_view_direct(self):
        self._create_ussd_group_questions()
        loop = mommy.make(QuestionLoop, loop_starter=Question.objects.first(),
                          loop_ender=Question.objects.last())
        self.assertTrue(QuestionLoop.objects.exists())
        url = reverse('remove_question_loop_page', args=(loop.id,))
        request = RequestFactory().get(url)
        request.user = self.user
        remove_loop(request, loop.id)
        self.assertFalse(QuestionLoop.objects.exists())

    def test_get_existing_response_validation_json(self):
        validation = mommy.make(ResponseValidation, validation_test='equals')
        arg = mommy.make(TextArgument, validation=validation, param=3, position=1)
        validation2 = mommy.make(ResponseValidation, validation_test='between')
        arg = mommy.make(TextArgument, validation=validation, param=12, position=1)
        arg = mommy.make(TextArgument, validation=validation, param=17, position=2)
        url = reverse('get_response_validations')
        response = self.client.get(url, data={'answer_type': TextAnswer.choice_name()})
        self.assertEquals(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertNotIn(validation2.id, response_data)
        self.assertIn(validation.id, response_data)

    def test_get_answer_validations(self):
        url = reverse('get_answer_validations')
        response = self.client.get(url, data={'answer_type': NumericalAnswer.choice_name()})
        self.assertEquals(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEquals(len(response_data), len(NumericalAnswer.validators()))
        numeric_validators = [v.__name__ for v in NumericalAnswer.validators()]
        for name in response_data:
            self.assertIn(name, numeric_validators)

    def test_add_to_question_library_with_multichoice(self):
        qset = self.qset
        data = {
            'answer_type': MultiChoiceAnswer.choice_name(),
            'text': 'multichoice answer text',
            'identifier': 'multi1_choice_identifier',
            'qset': qset.id,
            'options': ['Y', 'N'],
            'add_to_lib_button': '1'

        }
        url = reverse('new_qset_question_page', args=(self.qset.id, ))
        response = self.client.post(url, data=data)
        self.qset.refresh_from_db()
        self.assertTrue(TemplateOption.objects.exists())
        self.assertFalse(TemplateOption.objects.exclude(text__in=data['options']).exists())

    def test_attempt_create_invalid_multichoice_fails(self):
        qset = self.qset
        data = {
            'answer_type': MultiChoiceAnswer.choice_name(),
            'text': 'multichoice answer text',
            'identifier': 'multi1_choice_identifier',
            'qset': qset.id,
            'add_to_lib_button': '1'
        }
        url = reverse('new_qset_question_page', args=(self.qset.id,))
        response = self.client.post(url, data=data)
        self.assertFalse(response.context['questionform'].is_valid())

    def test_insert_set_question(self):
        self._create_ussd_non_group_questions()
        questions = self.qset.flow_questions
        self.assertEquals(len(questions), 4)
        question = questions[2]
        shifted = questions[3]
        url = reverse('insert_qset_question_page', args=(questions[2].id, ))
        data = {
            'answer_type': TextAnswer.choice_name(),
            'text': 'insert_data',
            'identifier': 'insert_text1_identifier',
            'qset': self.qset.id,

        }
        response = self.client.post(url, data=data)
        questions = self.qset.flow_questions
        self.assertEquals(len(questions), 5)
        self.assertEquals(questions[3].identifier, data['identifier'])
        self.assertEquals(questions[4], shifted)

    def test_get_assign_question_page(self):
        url = reverse('qset_assign_questions_page', args=(self.qset.id, ))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)        # self.qset is already assigned to interview in super setup
        qset = self.qset1
        url = reverse('qset_assign_questions_page', args=(qset.id, ))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_get_assign_to_new_qset(self):
        temp = mommy.make(QuestionTemplate)
        temp2 = mommy.make(QuestionTemplate)
        temp3 = mommy.make(QuestionTemplate)
        qset = self.qset1
        url = reverse('qset_assign_questions_page', args=(qset.id, ))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        data = dict()
        data['identifier'] = [temp.identifier, temp2.identifier]
        old_count = qset.questions.count()
        response = self.client.post(url, data=data)
        self.assertEquals(qset.questions.count(), old_count + 2)
        self.assertFalse(qset.questions.filter(identifier=temp3.identifier).exists())

    def test_get_assign_to_old_qset(self):
        temp = mommy.make(QuestionTemplate)
        temp2 = mommy.make(QuestionTemplate)
        temp3 = mommy.make(QuestionTemplate)
        qset = self.qset1
        self._create_ussd_non_group_questions(qset)
        url = reverse('qset_assign_questions_page', args=(qset.id, ))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        data = dict()
        data['identifier'] = [temp.identifier, temp2.identifier]
        old_count = qset.questions.count()
        response = self.client.post(url, data=data)
        self.assertEquals(qset.questions.count(), old_count + 2)
        self.assertFalse(qset.questions.filter(identifier=temp3.identifier).exists())

    def test_attempt_delete_question_with_answer(self):
        self._create_ussd_non_group_questions()
        question = Question.objects.filter(answer_type=NumericalAnswer.choice_name()).first()
        mommy.make(NumericalAnswer, question=question, interview=self.interview)
        url = reverse('remove_qset_question_page', args=(question.id, ))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Question.objects.filter(id=question.id).exists())

    def test_remove_loop(self):
        self._create_ussd_non_group_questions()
        all_questions = self.qset.all_questions
        loop = mommy.make(QuestionLoop, loop_starter=all_questions[1], loop_ender=all_questions[-1])
        url = reverse('remove_question_loop_page', args=(loop.id, ))
        self.assertEquals(QuestionLoop.objects.count(), 1)
        response = self.client.get(url)
        self.assertEquals(QuestionLoop.objects.count(), 0)

















