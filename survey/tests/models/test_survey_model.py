from django.test import TestCase
from survey.models.surveys import Survey


class SurveyTest(TestCase):

    def test_fields(self):
        survey = Survey()
        fields = [str(item.attname) for item in survey._meta.fields]
        self.assertEqual(len(fields), 7)
        for field in ['id', 'created', 'modified', 'name', 'description', 'rapid_survey', 'number_of_household_per_investigator']:
            self.assertIn(field, fields)

    def test_store(self):
        survey = Survey.objects.create(name="survey name", description="rajni survey")
        self.failUnless(survey.id)
        self.failUnless(survey.id)
        self.failUnless(survey.created)
        self.failUnless(survey.modified)
        self.assertFalse(survey.rapid_survey)
        self.assertEquals(10, survey.number_of_household_per_investigator)
