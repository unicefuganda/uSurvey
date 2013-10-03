from datetime import date
from django.test.testcases import TestCase
from survey.forms.surveys import SurveyForm

class SurveyFormTest(TestCase):
    def test_should_have_name_description_type_and_sample_size_fields(self):
        survey_form = SurveyForm()

        fields = ['name', 'description', 'type', 'sample_size']

        [self.assertIn(field, survey_form.fields) for field in fields]

    def test_should_not_be_valid_if_name_field_is_empty_or_blank(self):
        survey_form = SurveyForm()
        self.assertFalse(survey_form.is_valid())

    def test_should_be_valid_if_all_fields_are_given(self):
        form_data = {'name': 'xyz',
                     'description': 'survey description',
                     'sample_size': 10,
                     'type': True,
        }

        survey_form = SurveyForm(data=form_data)
        self.assertTrue(survey_form.is_valid())