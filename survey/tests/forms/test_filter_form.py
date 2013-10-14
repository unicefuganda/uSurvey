from django.test import TestCase
from survey.forms.question_filter import QuestionFilterForm
from survey.models import Question, QuestionModule, HouseholdMemberGroup


class QuestionFilterFormTest(TestCase):

    def test_form_instance_should_have_all_modules(self):
        module_1 = QuestionModule.objects.create(name="Module 1")
        module_2 = QuestionModule.objects.create(name="Module 2")
        module_3 = QuestionModule.objects.create(name="Module 2")

        question_filter_form = QuestionFilterForm()

        self.assertIn((module_1.id, module_1.name), question_filter_form.fields['modules'].choices)
        self.assertIn((module_2.id, module_2.name), question_filter_form.fields['modules'].choices)
        self.assertIn((module_3.id, module_3.name), question_filter_form.fields['modules'].choices)

    def test_form_instance_should_have_all_groups(self):
        group_1 = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        group_2 = HouseholdMemberGroup.objects.create(name="Group 2", order=2)
        group_3 = HouseholdMemberGroup.objects.create(name="Group 3", order=3)

        question_filter_form = QuestionFilterForm()

        all_groups = [group_1, group_2, group_3]

        [self.assertIn((group.id, group.name), question_filter_form.fields['groups'].choices) for group in all_groups]

    def test_form_instance_should_have_all_question_types(self):

        question_filter_form = QuestionFilterForm()

        all_question_types = [('number', 'Number'), ('text', 'Text'), ('multichoice', 'Multichoice')]

        [self.assertIn(question_type, question_filter_form.fields['question_types'].choices) for question_type in all_question_types]
