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
        question_module_form = QuestionModuleForm(
            data={'name': education_module.name})
        self.assertFalse(question_module_form.is_valid())
        error_message = "Module with name %s already exists." % education_module.name
        self.assertIn(error_message, question_module_form.errors['name'])

    def test_valid_if_instance_and_name_exists(self):
        education_module = QuestionModule.objects.create(name="Education")
        question_module_form = QuestionModuleForm(instance=education_module, data={'name': education_module.name,
                                                                                   'description': 'This is a description.'})
        self.assertTrue(question_module_form.is_valid())

    def test_invalid_if_instance_and_modified_name_exists(self):
        education_module = QuestionModule.objects.create(name="Education")
        health_module = QuestionModule.objects.create(name="Health")
        question_module_form = QuestionModuleForm(instance=education_module, data={'name': health_module.name,
                                                                                   'description': 'This is a description.'})
        self.assertFalse(question_module_form.is_valid())
        error_message = "Module with name %s already exists." % health_module.name
        self.assertIn(error_message, question_module_form.errors['name'])