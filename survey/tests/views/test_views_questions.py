import json
from django.test.client import Client
from django.contrib.auth.models import User
from mock import patch
from survey.models.batch import Batch
from survey.models.question import Question, QuestionOption

from survey.tests.base_test import BaseTest
from survey.forms.question import QuestionForm
from survey.models.householdgroups import HouseholdMemberGroup


class QuestionsViews(BaseTest):

    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'), 'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')
        self.household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)

        self.batch = Batch.objects.create(order = 1, name = "Batch A")
        self.question_1 = Question.objects.create(batch=self.batch, text="How many members are there in this household?",
                                            answer_type=Question.NUMBER, order=1)
        self.question_2 = Question.objects.create(batch=self.batch, text="How many of them are male?",
                                            answer_type=Question.NUMBER, order=2)

    def test_get_index_per_batch(self):
        response = self.client.get('/batches/%d/questions/'%self.batch.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('questions/index.html', templates)
        self.assertIn(self.question_1, response.context['questions'])
        self.assertIn(self.question_2, response.context['questions'])
        self.assertEqual(self.question_2.batch, response.context['batch'])
        self.assertIsNotNone(response.context['request'])

    @patch('django.contrib.messages.error')
    def test_no_questions_in_batch(self, mock_error):
        other_batch = Batch.objects.create(order=2, name="Other Batch")
        response = self.client.get('/batches/%d/questions/'%other_batch.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('questions/index.html', templates)
        self.assertEquals(0, len(response.context['questions']))
        self.assertEqual(other_batch, response.context['batch'])
        self.assertIsNotNone(response.context['request'])
        mock_error.assert_called_once_with(response.context['request'], 'There are no questions associated with this batch yet.')


    def test_add_new_question(self):
        response = self.client.get('/questions/new/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('questions/new.html', templates)
        self.assertIsInstance(response.context['questionform'], QuestionForm)

    def test_question_form_is_in_response_request_context(self):
        response = self.client.get('/questions/new/')
        self.assertIsInstance(response.context['questionform'], QuestionForm)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEqual(response.context['id'], 'add-question-form')

    def test_restricted_permissions(self):
        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        self.assert_restricted_permission_for("/questions/new/")
        self.assert_restricted_permission_for('/batches/%d/questions/'%self.batch.id)
        self.assert_restricted_permission_for('/questions/')
        self.assert_restricted_permission_for('/questions/groups/%d/'%member_group.id)

    @patch('django.contrib.messages.success')
    def test_create_question_number_does_not_create_options(self, mock_success):
        form_data={
                    'text': 'This is a Question',
                    'answer_type': Question.NUMBER,
                    'group' : self.household_member_group.id,
                    'options':'some option that should not be created',
                    }
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/questions/new/', data=form_data)
        question = Question.objects.filter(text=form_data['text'])
        self.failUnless(question)
        self.assertRedirects(response, expected_url='/questions/', status_code=302, target_status_code=200)
        question_options = question[0].options.all()
        self.assertEqual(0, question_options.count())

        assert mock_success.called

    def test_create_question_saves_order_based_on_group_created_for(self):
        form_data={
                'text': "This is a question",
                'answer_type': Question.NUMBER,
                'group' : self.household_member_group.id,
                'options': ''
                }
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/questions/new/', data=form_data)
        question = Question.objects.filter(text=form_data['text'])
        self.failUnless(question)
        self.assertEqual(1, question[0].order)

        form_data['text'] = 'This is another question'
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/questions/new/', data=form_data)
        question = Question.objects.filter(text=form_data['text'])
        self.failUnless(question)
        self.assertEqual(2, question[0].order)

        new_household_member_group = HouseholdMemberGroup.objects.create(name='Age 15-20', order=2)
        form_data['text'] = 'This is a question in new group'
        form_data['group'] = new_household_member_group.id
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/questions/new/', data=form_data)
        question = Question.objects.filter(text=form_data['text'])
        self.failUnless(question)
        self.assertEqual(1, question[0].order)


    def test_should_retrieve_group_specific_questions_in_context_if_selected_group_key_is_in_request(self):
        group_question = Question.objects.create(batch=self.batch, text="How many members are there in this household?",
                                            answer_type=Question.NUMBER, order=1,
                                            group=self.household_member_group)

        group_question_again = Question.objects.create(batch=self.batch, text="How many women are there in this household?",
                                            answer_type=Question.NUMBER, order=2,
                                            group=self.household_member_group)

        another_group_question = Question.objects.create(batch=self.batch, text="What is your name?",
                                            answer_type=Question.NUMBER, order=2,
                                            group=HouseholdMemberGroup.objects.create(name='Age 6-10', order=2))

        all_group_questions = [group_question, group_question_again]
        another_group_questions = [another_group_question]

        response = self.client.get('/batches/%d/questions/?group_id=%s'% (self.batch.id, self.household_member_group.id))

        questions = response.context["questions"]

        [self.assertIn(question, questions) for question in all_group_questions]
        [self.assertNotIn(question, questions) for question in another_group_questions]

    def test_should_retrieve_all_questions_in_context_if_selected_group_key_is_all_in_request(self):
        group_question = Question.objects.create(batch=self.batch, text="How many members are there in this household?",
                                            answer_type=Question.NUMBER, order=1,
                                            group=self.household_member_group)

        group_question_again = Question.objects.create(batch=self.batch, text="How many women are there in this household?",
                                            answer_type=Question.NUMBER, order=2,
                                            group=self.household_member_group)

        another_group_question = Question.objects.create(batch=self.batch, text="What is your name?",
                                            answer_type=Question.NUMBER, order=2,
                                            group=HouseholdMemberGroup.objects.create(name='Age 6-10', order=2))

        all_group_questions = [group_question, group_question_again, another_group_question]

        response = self.client.get('/batches/%d/questions/?group_id=%s'% (self.batch.id, 'all'))

        questions = response.context["questions"]

        [self.assertIn(question, questions) for question in all_group_questions]

    def test_should_retrieve_all_questions_as_data_for_filter_if_all_is_group_id_key(self):
        group_question = Question.objects.create(batch=self.batch, text="How many members are there in this household?",
                                            answer_type=Question.NUMBER, order=1,
                                            group=self.household_member_group)

        group_question_again = Question.objects.create(batch=self.batch, text="How many women are there in this household?",
                                            answer_type=Question.NUMBER, order=2,
                                            group=self.household_member_group)

        another_group_question = Question.objects.create(batch=self.batch, text="What is your name?",
                                            answer_type=Question.NUMBER, order=2,
                                            group=HouseholdMemberGroup.objects.create(name='Age 6-10', order=2))

        all_group_questions = [group_question, group_question_again, another_group_question]

        response = self.client.get('/questions/groups/%s/'% 'all')

        questions = json.loads(response.content)

        [self.assertIn(dict(text=question.text, id=question.id), questions) for question in all_group_questions]

    def test_should_retrieve_group_specific_questions_as_data_for_filter_if_group_id_key(self):
        group_question = Question.objects.create(batch=self.batch, text="How many members are there in this household?",
                                            answer_type=Question.NUMBER, order=1,
                                            group=self.household_member_group)

        group_question_again = Question.objects.create(batch=self.batch, text="How many women are there in this household?",
                                            answer_type=Question.NUMBER, order=2,
                                            group=self.household_member_group)

        another_group_question = Question.objects.create(batch=self.batch, text="What is your name?",
                                            answer_type=Question.NUMBER, order=2,
                                            group=HouseholdMemberGroup.objects.create(name='Age 6-10', order=2))

        all_group_questions = [group_question, group_question_again]
        another_all_group_questions = [another_group_question]

        response = self.client.get('/questions/groups/%s/'% self.household_member_group.id)

        questions = json.loads(response.content)

        [self.assertIn(dict(text=question.text, id=question.id), questions) for question in all_group_questions]
        [self.assertNotIn(dict(text=question.text, id=question.id), questions) for question in another_all_group_questions]

    def test_should_save_options_for_multichoice_questions(self):
        form_data={
            'text': 'This is a Question',
            'answer_type': Question.MULTICHOICE,
            'group' : self.household_member_group.id,
            'options':['some question option 1', 'some question option 2'],
            }
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/questions/new/', data=form_data)
        question = Question.objects.filter(text=form_data['text'])
        self.failUnless(question)
        self.assertEqual(1, len(question))
        self.assertRedirects(response, expected_url='/questions/', status_code=302, target_status_code=200)
        question_options = question[0].options.all()
        self.assertEqual(2, question_options.count())
        self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), question_options )
        self.assertIn(QuestionOption.objects.get(text=form_data['options'][1]), question_options )

    def test_should_not_save_empty_options_on_multichoice_questions(self):
        form_data={
            'text': 'This is a Question',
            'answer_type': Question.MULTICHOICE,
            'group' : self.household_member_group.id,
            'options':['some question option 1', '', 'some question option 2', ''],
            }
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/questions/new/', data=form_data)
        question = Question.objects.filter(text=form_data['text'])
        self.failUnless(question)
        self.assertEqual(1, len(question))
        self.assertRedirects(response, expected_url='/questions/', status_code=302, target_status_code=200)
        question_options = question[0].options.all()
        self.assertEqual(2, question_options.count())
        self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), question_options )
        self.assertIn(QuestionOption.objects.get(text=form_data['options'][2]), question_options )

    def test_should_not_save_multichoice_questions_if_no_option_supplied(self):
        form_data={
            'text': 'This is a Question',
            'answer_type': Question.MULTICHOICE,
            'group' : self.household_member_group.id,
            'options':'',
            }
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/questions/new/', data=form_data)
        self.failUnlessEqual(response.status_code, 200)
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)

    def test_should_not_save_options_if_question_not_multichoice_even_if_options_supplied(self):
        form_data={
                'text': 'This is a Question',
                'answer_type': Question.TEXT,
                'group' : self.household_member_group.id,
                'options':['some question option 1', 'some question option 2'],
                }
        question = Question.objects.filter(text=form_data['text'])
        self.failIf(question)
        response = self.client.post('/questions/new/', data=form_data)
        question = Question.objects.filter(text=form_data['text'])
        self.failUnless(question)
        self.assertEqual(1, len(question))
        self.assertRedirects(response, expected_url='/questions/', status_code=302, target_status_code=200)
        question_options = question[0].options.all()
        self.assertEqual(0, question_options.count())

    def test_should_render_json_questions_filtered_by_group(self):
        member_group = HouseholdMemberGroup.objects.create(name="0 to 6 years", order=0)
        question_1 = Question.objects.create(text="question1", answer_type=Question.NUMBER, group=member_group)
        question_2 = Question.objects.create(text="question2", answer_type=Question.NUMBER)
        response = self.client.get('/questions/groups/%d/'%member_group.id)
        self.failUnlessEqual(response.status_code, 200)

        content = json.loads(response.content)
        self.assertEquals(len(content), 1)

        self.assertEquals(content[0]['id'], question_1.pk)
        self.assertEquals(content[0]['text'], question_1.text)

    def test_get_index_all(self):
        response = self.client.get('/questions/')
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('questions/index.html', templates)
        self.assertIn(self.question_1, response.context['questions'])
        self.assertIn(self.question_2, response.context['questions'])
        self.assertIsNotNone(response.context['request'])