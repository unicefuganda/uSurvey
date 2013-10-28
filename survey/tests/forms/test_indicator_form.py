from django.test import TestCase
from survey.forms.indicator import IndicatorForm
from survey.models import QuestionModule, Batch


class IndicatorFormTest(TestCase):
    def setUp(self):
        module = QuestionModule.objects.create(name="Health")
        batch = Batch.objects.create(name="Health")

        self.form_data = {'module': module.id,
                          'name': 'Health',
                          'description': 'some description',
                          'measure': '%',
                          'batch': batch.id}

    def test_valid(self):
        indicator_form = IndicatorForm(self.form_data)
        self.assertTrue(indicator_form.is_valid())

    def test_invalid(self):
        form_data = self.form_data.copy()
        form_data['module'] = ''
        indicator_form = IndicatorForm(form_data)
        self.assertFalse(indicator_form.is_valid())
        self.assertEqual(['This field is required.'], indicator_form.errors['module'])