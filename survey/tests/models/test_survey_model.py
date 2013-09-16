from django.test import TestCase
from survey.models.surveys import Survey


class SurveyTest(TestCase):

    def test_fields(self):
        survey = Survey()
        fields = [str(item.attname) for item in survey._meta.fields]
        self.assertEqual(7, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'description', 'type', 'sample_size']:
            self.assertIn(field, fields)

    def test_store(self):
        survey = Survey.objects.create(name="survey name", description="rajni survey")
        self.failUnless(survey.id)
        self.failUnless(survey.id)
        self.failUnless(survey.created)
        self.failUnless(survey.modified)
        self.assertFalse(survey.type)
        self.assertEquals(10, survey.sample_size)
