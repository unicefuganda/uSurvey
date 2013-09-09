from django.test import TestCase
from survey.forms.question import *
from survey.models import *

class QuestionFormTest(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(name='Batch A',description='description')
        self.household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)

        self.form_data = {
                        'batch': self.batch.id,
                        'text': 'whaat?',
                        'answer_type': Question.NUMBER,
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



