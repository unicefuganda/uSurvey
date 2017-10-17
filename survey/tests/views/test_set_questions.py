import json
from model_mommy import mommy
from django.contrib.auth.models import User
from model_mommy import mommy
from django.test.client import Client
from django.core.urlresolvers import reverse
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import *
from survey.utils.query_helper import get_filterset
from survey.tests.base_test import BaseTest


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
            name='survey name', description='survey descrpition')
        batch_obj = Batch.objects.create(
            order=1, name="Batch A", survey=survey_obj)
        list_1 = ListingTemplate.objects.create(name="List A9")
        qset = QuestionSet.get(pk=list_1.id)
        response = self.client.get(reverse('add_qset_subquestion_page', kwargs={"batch_id" : qset.id}))
        self.assertIn(response.status_code, [200, 302])
        templates = [ template.name for template in response.templates ]
        self.assertIn('set_questions/_add_question.html', templates)
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
        list_1 = ListingTemplate.objects.create(name="List b2")
        qset = QuestionSet.get(pk=list_1.id)
        q_obj = Question.objects.create(identifier='id_1', text="This is a question123.5", answer_type='Numerical Answer',
                                                  qset_id=qset.id, response_validation_id=self.rsp.id)
        response = self.client.get(reverse('questions_subquestion_json_page', kwargs={"question_id" : list_1.id}))
        self.assertIn(response.status_code,[200,302])

    def test_get_prev_questions_for_question(self):
        self.qset = QuestionSet.objects.create(name="Females")
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest", constraint_message="message")
        self.question_1 = Question.objects.create(identifier='id_1', text="This is a question 1111.1",
                                                  answer_type='Numerical Answer',
                                                  qset_id=self.qset.id, response_validation_id=self.rsp.id)
        response = self.client.get(reverse('prev_inline_questions_json_page',
                                           kwargs={"question_id" : self.question_1.id}))
        self.assertIn(response.status_code, [200, 302])

    def test_delete(self):
        list_1 = ListingTemplate.objects.create(name="List b3")
        qset = QuestionSet.get(pk=list_1.id)
        q_obj = Question.objects.create(identifier='id_2', text="This is a question123.6",
                                        answer_type='Numerical Answer', qset_id=qset.id,
                                        response_validation_id=self.rsp.id)
        response = self.client.get(reverse('delete_question_page', kwargs={"question_id" : list_1.id}))
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
        list_1 = ListingTemplate.objects.create(name="List b4")
        qset = QuestionSet.get(pk=list_1.id)
        q_obj = Question.objects.create(identifier='id_3', text="This is a question123.7",
                                        answer_type='Numerical Answer',
                                        qset_id=qset.id, response_validation_id=self.rsp.id)
        response = self.client.get(reverse('remove_qset_question_page', kwargs={"question_id" : list_1.id}))
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
        batch_obj = Batch.objects.create(name='b1900010w',description='d1', survey=survey_obj)
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
        batch_obj = Batch.objects.create(name='b1900010w11',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        url = reverse('qset_assign_questions_page', kwargs={"qset_id": qset.id})
        response = self.client.post(url, data={"identifier": "identifier_demo"})
        self.assertRedirects(response, expected_url= reverse('qset_questions_page',
                                                             kwargs={"qset_id": qset.id}), msg_prefix='')
        self.assertIn("Questions successfully assigned to Batch: %s." % batch_obj.name,
                      response.cookies['messages'].__str__())
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
        self.assertRedirects(response, expected_url= reverse('qset_questions_page', kwargs={"qset_id" : qset.id}), msg_prefix='')

    def test_qset_assign_questions_page_assign(self):
        listing_form = ListingTemplate.objects.create(name='l12xa11', description='desc1')
        kwargs = {'name': 'survey11uz11ww', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(name='b1900010w',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
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
        ans_args = (interview_obj, question1, option1_text)
        answer_class = Answer.get_class(question1.answer_type)
        ans_obj = answer_class.create(*ans_args)
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
        url = reverse('qset_assign_questions_page', kwargs={"qset_id" : qset.id})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        self.assertRedirects(response, expected_url= reverse('qset_questions_page', kwargs={"qset_id" : qset.id}), msg_prefix='')
        # self.assertIn("Questions cannot be assigned \
        #     interviews has already been conducted: %s."%batch_obj.name, response.cookies['messages'].__str__())

        
        batch_obj = Batch.objects.create(name='b1900010w11',description='d1', survey=survey_obj)
        qset = QuestionSet.get(id=batch_obj.id)
        
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        url = reverse('qset_assign_questions_page', kwargs={"qset_id" : qset.id})
        response = self.client.post(url, data={"identifier" : "identifier_demo"})
        self.assertRedirects(response, expected_url= reverse('qset_questions_page', kwargs={"qset_id" : qset.id}), msg_prefix='')
        self.assertIn("Questions successfully assigned to Batch: %s."%batch_obj.name, response.cookies['messages'].__str__())
        self.assertRedirects(response, expected_url= reverse('qset_questions_page', kwargs={"qset_id" : qset.id}), msg_prefix='')





