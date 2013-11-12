from django.test import TestCase
from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.surveys import SurveyForm
from survey.models import Batch, Investigator, Backend
from survey.models.surveys import Survey


class SurveyTest(TestCase):

    def test_fields(self):
        survey = Survey()
        fields = [str(item.attname) for item in survey._meta.fields]
        self.assertEqual(8, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'description', 'type', 'has_sampling', 'sample_size']:
            self.assertIn(field, fields)

    def test_store(self):
        survey = Survey.objects.create(name="survey name", description="rajni survey")
        self.failUnless(survey.id)
        self.failUnless(survey.id)
        self.failUnless(survey.created)
        self.failUnless(survey.modified)
        self.assertFalse(survey.type)
        self.assertEquals(10, survey.sample_size)
        self.assertTrue(survey.has_sampling)

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

    def test_saves_survey_with_sample_size_from_form_if_has_sampling_is_true(self):
        form_data = {
            'name': 'survey rajni',
            'description': 'survey description rajni',
            'has_sampling': True,
            'sample_size': 10,
            'type': True,
        }
        survey_form = SurveyForm(data=form_data)
        Survey.save_sample_size(survey_form)
        saved_survey = Survey.objects.filter(name=form_data['name'], has_sampling=form_data['has_sampling'])
        self.failUnless(saved_survey)
        self.assertEqual(form_data['sample_size'], saved_survey[0].sample_size)

    def test_saves_survey_with_sample_size_zero_if_has_sampling_is_false(self):
        form_data = {
            'name': 'survey rajni',
            'description': 'survey description rajni',
            'has_sampling': False,
            'sample_size': 10,
            'type': True,
        }
        survey_form = SurveyForm(data=form_data)
        Survey.save_sample_size(survey_form)
        saved_survey = Survey.objects.filter(name=form_data['name'], has_sampling=form_data['has_sampling'])
        self.failUnless(saved_survey)
        self.assertEqual(0, saved_survey[0].sample_size)

    def test_unicode_text(self):
        survey = Survey.objects.create(name="survey name", description="rajni survey")
        self.assertEqual(survey.name, str(survey))

    def test_knows_currently_open_survey(self):

        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)

        open_survey = Survey.objects.create(name="open survey", description="open survey")
        closed_survey = Survey.objects.create(name="closed survey", description="closed survey")
        another_closed_survey = Survey.objects.create(name="another closed survey", description="another closed survey")

        open_batch = Batch.objects.create(order=1, name="Open Batch", survey=open_survey)
        closed_batch = Batch.objects.create(order=2, name="Closed Batch", survey=closed_survey)
        another_closed_batch = Batch.objects.create(order=3, name="Another Closed Batch", survey=another_closed_survey)

        open_batch.open_for_location(kampala)

        self.assertEqual(open_survey, Survey.currently_open_survey())
        self.assertNotEqual(closed_survey, Survey.currently_open_survey())
        self.assertNotEqual(another_closed_survey, Survey.currently_open_survey())

    def test_returns_none_if_there_is_no_currently_open_survey(self):

        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)

        open_survey = Survey.objects.create(name="open survey", description="open survey")
        closed_survey = Survey.objects.create(name="closed survey", description="closed survey")
        another_closed_survey = Survey.objects.create(name="another closed survey", description="another closed survey")

        open_batch = Batch.objects.create(order=1, name="Open Batch", survey=open_survey)
        closed_batch = Batch.objects.create(order=2, name="Closed Batch", survey=closed_survey)
        another_closed_batch = Batch.objects.create(order=3, name="Another Closed Batch", survey=another_closed_survey)

        self.assertEqual(None, Survey.currently_open_survey())

    def test__survey_knows_is_currently_open_for_location(self):

        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        masaka = Location.objects.create(name="masaka", type=district, tree_parent=uganda)
        wakiso = Location.objects.create(name="wakiso", type=district, tree_parent=uganda)

        open_survey = Survey.objects.create(name="open survey", description="open survey")

        open_batch = Batch.objects.create(order=1, name="Open Batch", survey=open_survey)
        open_batch_2 = Batch.objects.create(order=2, name="Open Batch 2", survey=open_survey)
        open_batch.open_for_location(kampala)
        open_batch_2.open_for_location(masaka)
        self.assertTrue(open_survey.is_open_for(kampala))
        self.assertTrue(open_survey.is_open_for(masaka))
        self.assertFalse(open_survey.is_open_for(wakiso))

    def test_survey_knows_opened_for_parent_means_opened_for_children(self):

        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        masaka = Location.objects.create(name="masaka", type=district, tree_parent=uganda)

        open_survey = Survey.objects.create(name="open survey", description="open survey")

        open_batch = Batch.objects.create(order=1, name="Open Batch", survey=open_survey)
        open_batch.open_for_location(uganda)
        self.assertTrue(open_survey.is_open_for(kampala))
        self.assertTrue(open_survey.is_open_for(masaka))
