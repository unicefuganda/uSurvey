from django.test import TestCase
from survey.forms.question import *
from survey.models import Batch
from survey.models.question import Question
from survey.models.householdgroups import HouseholdMemberGroup


class QuestionFormTest(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(name='Batch A',description='description')
        self.household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)

        self.form_data = {
                        'batch': self.batch.id,
                        'text': 'whaat?',
                        'answer_type': Question.NUMBER,
                        'options':"some option text",
                        'group' : self.household_member_group.id
        }

    def test_valid(self):
        question_form = QuestionForm(self.form_data)
        question_form.is_valid()
        self.assertTrue(question_form.is_valid())

    def test_invalid(self):
        question_form = QuestionForm()
        self.assertFalse(question_form.is_valid())

    def test_question_form_fields(self):
        question_form = QuestionForm()
        fields = ['text', 'answer_type', 'group']
        [self.assertIn(field, question_form.fields) for field in fields]

    def test_should_know_household_member_group_id_and_name_tuple_is_the_group_choice(self):
        question_form = QuestionForm(self.form_data)
        self.assertEqual(question_form.fields['group'].choices, [(self.household_member_group.id, self.household_member_group.name)])

    def test_should_not_save_multichoice_question_if_no_options_given(self):
        form_data = self.form_data.copy()
        form_data['answer_type'] = Question.MULTICHOICE
        form_data['options']=''
        question_form = QuestionForm(form_data)
        self.assertFalse(question_form.is_valid())
        expected_form_error = 'Question Options missing.'
        self.assertEqual(1, len(question_form.errors['answer_type']))
        self.assertEqual(expected_form_error, question_form.errors['answer_type'][0])

    def test_should_save_options_and_batch_attached_to_questions_if_supplied(self):
        form_data = self.form_data.copy()
        form_data['answer_type'] = Question.MULTICHOICE
        form_data['options']=['option 1', 'option 2']
        question_form = QuestionForm(form_data)
        self.assertTrue(question_form.is_valid())
        batch = Batch.objects.create()
        question = question_form.save(batch=batch, group=[self.household_member_group.id])
        self.assertEqual(batch, question.batch)
        options = question.options.all()
        self.assertEqual(2, options.count())
        self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), options)
        self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), options)

    def test_should_save_questions_and_options_even_if_batch_is_not_supplied(self):
        form_data = self.form_data.copy()
        form_data['answer_type'] = Question.MULTICHOICE
        form_data['options']=['option 1', 'option 2']
        question_form = QuestionForm(form_data)
        self.assertTrue(question_form.is_valid())
        question = question_form.save(group=[self.household_member_group.id])
        self.assertIsNone(question.batch)
        options = question.options.all()
        self.assertEqual(2, options.count())
        self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), options)
        self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), options)

    def test_should_not_save_options_if_not_multichoice_even_if_options_supplied(self):
        form_data = self.form_data.copy()
        form_data['answer_type'] = Question.TEXT
        form_data['options']=['some option question']
        question_form = QuestionForm(form_data)
        self.assertTrue(question_form.is_valid())
        question = question_form.save(group=[self.household_member_group.id])
        self.assertIsNone(question.batch)
        self.assertEquals(0, question.options.all().count())

    def test_should_filter_options_not_supplied(self):
        form_data = self.form_data.copy()
        form_data['answer_type'] = Question.TEXT
        del form_data['options']
        question_form = QuestionForm(form_data)
        self.assertTrue(question_form.is_valid())
        question = question_form.save(group=[self.household_member_group.id])
        self.assertIsNone(question.batch)
        self.assertEquals(0, question.options.all().count())

    def test_form_should_not_be_valid_for_subquestion_if_same_subquestion_already_exist(self):
       question = Question.objects.create(batch=self.batch, text="Question 1?",
                                                answer_type=Question.NUMBER, order=1,group=self.household_member_group)
       sub_question = Question.objects.create(text="this is a sub question", answer_type=Question.NUMBER,
                                               batch=self.batch, subquestion=True, parent=question,group=self.household_member_group)
       form_data = self.form_data.copy()
       form_data['text'] = sub_question.text
       form_data['answer_type'] = sub_question.answer_type
       del form_data['options']
       question_form = QuestionForm(data=form_data, parent_question=sub_question.parent)
       self.assertFalse(question_form.is_valid())
       message= "Sub question for this question with this text already exists."
       self.assertIn(message, question_form.errors.values()[0])
