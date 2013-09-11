from datetime import date
from django.test.testcases import TestCase
from survey.forms.surveys import SurveyForm
from survey.models.question import Question

class SurveyFormTest(TestCase):
    def test_should_have_name_description_rapid_survey_fields(self):
        survey_form = SurveyForm()

        fields = ['name', 'description', 'rapid_survey', 'number_of_household_per_investigator', 'questions']

        [self.assertIn(field, survey_form.fields) for field in fields]

    def test_should_not_be_valid_if_name_field_is_empty_or_blank(self):
        survey_form = SurveyForm()
        self.assertFalse(survey_form.is_valid())

    def test_should_be_valid_if_all_fields_are_given(self):
        question = Question.objects.create()
        form_data = {'name': 'xyz',
                     'description': 'survey description',
                     'number_of_household_per_investigator': 10,
                     'rapid_survey': True,
                     'questions':[question.pk]
        }

        survey_form = SurveyForm(data=form_data)
        self.assertTrue(survey_form.is_valid())