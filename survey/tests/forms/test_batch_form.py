from django.test import TestCase
from survey.forms.batch import *

class BatchFormTest(TestCase):
    def test_valid(self):
        form_data = {
                        'name': 'Batch 1',
                        'description': 'description goes here',
                    }
        batch_form = BatchForm(form_data)
        self.assertTrue(batch_form.is_valid())

    def test_invalid(self):
        form_data = {
                        'description': 'description goes here',
                    }
        batch_form = BatchForm(form_data)
        self.assertFalse(batch_form.is_valid())

    def test_form_should_be_invalid_if_name_already_exists(self):
        Batch.objects.create(name='Batch A',description='description')
        form_data = {
                        'name': 'Batch A',
                        'description': 'description goes here',
                    }
        batch_form = BatchForm(form_data)
        self.assertFalse(batch_form.is_valid())
        self.assertIn('Batch with the same name already exist', batch_form.errors['name'])
