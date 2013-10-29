from django.test import TestCase
from rapidsms.contrib.locations.models import Location
from survey.models import Batch, Investigator, Backend
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

    def test_survey_knows_it_is_open(self):
        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number='123456789',
                                                        location=Location.objects.create(name="Kampala"),
                                                        backend=Backend.objects.create(name='something'))

        survey = Survey.objects.create(name="survey name", description="rajni survey")
        batch = Batch.objects.create(order=1, survey=survey)

        batch.open_for_location(self.investigator.location)

        self.assertTrue(survey.is_open())

    def test_survey_knows_it_is_closed(self):
        self.investigator = Investigator.objects.create(name="investigator name",
                                                        mobile_number='123456789',
                                                        location=Location.objects.create(name="Kampala"),
                                                        backend=Backend.objects.create(name='something'))

        survey = Survey.objects.create(name="survey name", description="rajni survey")

        Batch.objects.create(order=1, survey=survey)

        self.assertFalse(survey.is_open())

    def test_unicode_text(self):
        survey = Survey.objects.create(name="survey name", description="rajni survey")
        self.assertEqual(survey.name, str(survey))