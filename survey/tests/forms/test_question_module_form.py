from django.test import TestCase
from survey.forms.question_module_form import QuestionModuleForm
from survey.models import QuestionModule


class QuestionModuleFormTest(TestCase):
    def test_valid(self):
        form_data = {
                        'name': 'Education',
                    }
        question_module_form = QuestionModuleForm(form_data)
        self.assertTrue(question_module_form.is_valid())

    def test_invalid(self):
        question_module_form = QuestionModuleForm({'name': ''})
        self.assertFalse(question_module_form.is_valid())

    def test_module_invalid_if_name_already_exists(self):
        education_module = QuestionModule.objects.create(name="Education")
        question_module_form = QuestionModuleForm({'name': education_module.name })
        self.assertFalse(question_module_form.is_valid())
        error_message = "Module with name %s already exists." % education_module.name
        self.assertIn(error_message, question_module_form.errors['name'])