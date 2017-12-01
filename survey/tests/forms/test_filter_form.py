from model_mommy import mommy
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from survey.models import *
from survey.forms.filters import *


class QuestionFilterFormTest(TestCase):

    def test_form_instance_should_have_all_question_types(self):
        question_filter_form = QuestionFilterForm()
        all_question_types = [('Numerical Answer', 'Numerical Answer'), (
            'Text Answer', 'Text Answer'), ('Multi Choice Answer', 'Multi Choice Answer')]
        [self.assertIn(question_type, question_filter_form.fields[
                       'question_types'].choices) for question_type in all_question_types]

    def test_questions_filter_fields(self):
        form = QuestionFilterForm(read_only=['question_types', ])
        self.assertTrue(form.fields['question_types'].widget.attrs['readonly'])
        self.assertTrue(form.fields['question_types'].widget.attrs['disabled'])

    def test_batch_questions_filter_disable_fields(self):
        form = BatchQuestionFilterForm(read_only=['question_types', ])
        self.assertTrue(form.fields['question_types'].widget.attrs['readonly'])
        self.assertTrue(form.fields['question_types'].widget.attrs['disabled'])


class IndicatorFilterFormTest(TestCase):
    
    def setUp(self):
        self.module_1 = QuestionModule.objects.create(name="Module 1")
        self.module_2 = QuestionModule.objects.create(name="Module 2")
        self.module_3 = QuestionModule.objects.create(name="Module 3")
        self.survey = Survey.objects.create(name="Survey A")
        self.survey_2 = Survey.objects.create(name="Survey B")
        self.batch = Batch.objects.create(name="Batch A", survey=self.survey)
        self.batch_1 = Batch.objects.create(name="Batch B", survey=self.survey)
        self.batch_3 = Batch.objects.create(
            name="Batch C", survey=self.survey_2)
        self.batch_4 = Batch.objects.create(
            name="Batch D", survey=self.survey_2)

    def test_form_instance_should_have_all_surveys(self):
        indicator_filter_form = IndicatorFilterForm()
        self.assertEqual(
            3, len(indicator_filter_form.fields['survey'].choices))
        self.assertIn((self.survey.id, self.survey.name),
                      indicator_filter_form.fields['survey'].choices)
        self.assertIn((self.survey_2.id, self.survey_2.name),
                      indicator_filter_form.fields['survey'].choices)

    def test_form_should_show_batches_under_a_survey_only_if_survey_given(self):
        indicator_filter_form = IndicatorFilterForm(
            data={'survey': str(self.survey.id), 'question_set': 'All'})
        self.assertEqual(3, len(indicator_filter_form.fields['question_set'].choices))
        self.assertIn((self.batch_1.id, self.batch_1.name),
                      indicator_filter_form.fields['question_set'].choices)
        self.assertIn((self.batch.id, self.batch.name),
                      indicator_filter_form.fields['question_set'].choices)

    def test_invalid_survey_choices(self):
        indicator_filter_form = IndicatorFilterForm(
            data={'survey': 'ayoyoyoyoooo', 'batch': str(self.batch.id)})
        self.assertFalse(indicator_filter_form.is_valid())
        self.assertEqual(['Select a valid choice. ayoyoyoyoooo is not one of the available choices.'],
                         indicator_filter_form.errors['survey'])

    def test_invalid_batch_choices(self):
        indicator_filter_form = IndicatorFilterForm(
            data={'survey': str(self.survey.id), 'batch': 'ayoyoyooooooo'})
        self.assertTrue(indicator_filter_form.is_valid())
        # self.assertEqual(['Select a valid choice. ayoyoyooooooo is not one of the available choices.'],
        #                  indicator_filter_form.errors['batch'])

    def test_only_survey_batches_are_allowed(self):
        bacth_id_not_belongin_got_self_survey = str(self.batch_3.id)
        data = {'survey': str(self.survey.id),
                'batch': bacth_id_not_belongin_got_self_survey}
        indicator_filter_form = IndicatorFilterForm(data=data)
        self.assertTrue(indicator_filter_form.is_valid())


class SurveyBatchFilterFormTest(TestCase):

    def setUp(self):
        self.survey = Survey.objects.create(name="Survey A")
        self.survey_2 = Survey.objects.create(name="Survey B")
        self.batch = Batch.objects.create(name="Batch A", survey=self.survey)
        self.batch_1 = Batch.objects.create(
            name="Batch B", survey=self.survey_2)
        self.data = {'survey': self.survey.id,
                     'batch': self.batch.id,
                     'multi_option': 1}

    def test_valid(self):
        survey_batch_filter_form = SurveyBatchFilterForm(self.data)
        self.assertTrue(survey_batch_filter_form.is_valid())

    def test_empty_batch_is_valid(self):
        data = self.data.copy()
        data['batch'] = ''
        survey_batch_filter_form = SurveyBatchFilterForm(data)
        self.assertTrue(survey_batch_filter_form.is_valid())

    def assert_invalid_if_field_does_not_exist(self, field_key):
        form_data = self.data.copy()
        non_existing_survey_id = 666
        form_data[field_key] = non_existing_survey_id
        survey_batch_filter_form = SurveyBatchFilterForm(form_data)
        self.assertFalse(survey_batch_filter_form.is_valid())
        message = "Select a valid choice. That choice is not one of the available choices."
        self.assertEqual([message], survey_batch_filter_form.errors[field_key])

    def assert_invalid_if_field_is_non_sense(self, field_key):
        form_data = self.data.copy()
        form_data[field_key] = 'non_sense_hohoho_&^%$#'
        survey_batch_filter_form = SurveyBatchFilterForm(form_data)
        self.assertFalse(survey_batch_filter_form.is_valid())
        message = "Select a valid choice. That choice is not one of the available choices."
        self.assertEqual([message], survey_batch_filter_form.errors[field_key])

    def test_invalid_if_batch_is_not_under_survey(self):
        form_data = self.data.copy()
        form_data['survey'] = self.survey.id
        form_data['batch'] = self.batch_1.id
        survey_batch_filter_form = SurveyBatchFilterForm(form_data)
        self.assertFalse(survey_batch_filter_form.is_valid())
        message = "Select a valid choice. That choice is not one of the available choices."
        self.assertEqual([message], survey_batch_filter_form.errors['batch'])


class BatchOpenStatusFilterFormTestExtra(TestCase):
    fixtures = ['enumeration_area', 'locations', 'location_types', ]

    def test_form_invalid_returns_all_locations(self):
        batch = mommy.make(Batch)
        form = BatchOpenStatusFilterForm(batch=batch, data={'status': 'something'})
        self.assertFalse(form.is_valid())
        self.assertEquals(form.get_locations().count(),
                          Location.objects.filter(type=LocationType.largest_unit()).count())
        # now check since we havent opened any, count should be same as closed form
        form = BatchOpenStatusFilterForm(batch=batch, data={'status': form.CLOSED})
        self.assertEquals(form.get_locations().count(),
                          Location.objects.filter(type=LocationType.largest_unit()).count())
        BatchLocationStatus.objects.create(batch=batch,
                                           location=Location.objects.filter(type=LocationType.largest_unit()).last())
        # confirm this cannot be seen afte the location has been open
        form = BatchOpenStatusFilterForm(batch=batch, data={'status': form.CLOSED})
        self.assertEquals(form.get_locations().count(), 0)
        form = BatchOpenStatusFilterForm(batch=batch, data={'status': form.OPEN})
        self.assertEquals(form.get_locations().count(),
                          Location.objects.filter(type=LocationType.largest_unit()).count())


class UserFormFilterExtra(TestCase):

    def test_filter_user_by_status(self):
        user1 = mommy.make(User, is_active=False)
        user2 = mommy.make(User, is_active=False)
        user3 = mommy.make(User, is_active=True)
        user_form = UsersFilterForm()
        self.assertEquals(user_form.get_users().distinct().count(), 3)
        user_form = UsersFilterForm(data={'status': user_form.ACTIVE})
        self.assertEquals(user_form.get_users().distinct().count(), 1)
        user_form = UsersFilterForm(data={'status': user_form.DEACTIVATED})
        self.assertEquals(user_form.get_users().distinct().count(), 2)
        user_form = UsersFilterForm(data={'status': 'balaba'})
        self.assertFalse(user_form.is_valid())
        self.assertEquals(user_form.get_users().distinct().count(), 3)


class FilterFormTestExtra(TestCase):

    fixtures = ['enumeration_area', 'locations', 'location_types', 'contenttypes', 'groups', 'permissions',
                'answeraccessdefinition.json']

    def setUp(self):
        # locad parameters required
        #
        self.ea = EnumerationArea.objects.first()
        self.interviewer = mommy.make(Interviewer)
        self.qset = mommy.make(ListingTemplate)
        self.survey = mommy.make(Survey, has_sampling=True, listing_form=self.qset)
        self.qset1 = mommy.make(Batch, name='TestNewQset', survey=self.survey)
        self.access_channel = mommy.make(ODKAccess, interviewer=self.interviewer)
        self.interview = mommy.make(Interview, interviewer=self.interviewer, survey=self.survey, ea=self.ea,
                                    interview_channel=self.access_channel, question_set=self.qset)

    def test_form_qset_without_survey(self):
        survey1 = mommy.make(Survey, name='test1')
        survey2 = mommy.make(Survey, name='test2')
        form = QuestionSetResultsFilterForm(self.qset)
        # confirm only applies to relevant survey only
        self.assertEquals(form.fields['survey'].queryset.exclude(pk=self.survey.pk).count(), 0)
        form = QuestionSetResultsFilterForm(self.qset, data={'survey': self.survey.id})
        self.assertEquals(form.get_interviews().count(), 1)

    def test_form_survey_results_form_filter_disabled_listing(self):
        form = SurveyResultsFilterForm(ListingTemplate, disabled_fields=['question_set', ],
                                       data={'question_set': self.qset.id,
                                             'from_date': (timezone.now() - timedelta(days=5)
                                                           ).strftime(settings.DATE_FORMAT),
                                             'to_date': (timezone.now() +
                                                         timedelta(days=5)).strftime(settings.DATE_FORMAT)})
        self.assertEquals(form.get_interviews().count(), 1)
        form = SurveyResultsFilterForm(ListingTemplate, disabled_fields=['question_set', ],
                                       data={'question_set': self.qset.id,
                                             'from_date': (timezone.now() -
                                                           timedelta(days=10)).strftime(settings.DATE_FORMAT),
                                             'to_date': (timezone.now() -
                                                         timedelta(days=5)).strftime(settings.DATE_FORMAT)})
        self.assertEquals(form.get_interviews().count(), 0)



