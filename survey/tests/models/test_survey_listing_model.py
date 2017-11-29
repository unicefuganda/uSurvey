import string
from model_mommy import mommy
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test.client import Client
from survey.tests.base_test import BaseTest
from survey.models.base import BaseModel
from survey.models import Question, QuestionSet
from survey.models import Answer, MultiChoiceAnswer
from survey.templatetags.template_tags import get_sample_data_display
from survey.models.surveys import Survey
from survey.models import Interview, SurveyAllocation, Interviewer, ListingSample
from survey.models import ListingTemplate, RandomizationCriterion, CriterionTestArgument, ODKAccess, QuestionSetChannel
from survey.models import EnumerationArea, NumericalAnswer, MultiChoiceAnswer, TextAnswer
from survey.tests.models.survey_base_test import SurveyBaseTest


class RandomizationTest(SurveyBaseTest):
    
    def setUp(self):
        self.qset = ListingTemplate.objects.create(name="raja")
        self.survey = Survey.objects.create(name="haha", has_sampling=True, sample_size=3,
                                            listing_form=self.qset)
        # create the access channel
        self.qset_channels = mommy.make(QuestionSetChannel, qset=self.qset, channel=ODKAccess.choice_name())
        self.ea = EnumerationArea.objects.last()
        self.interviewer = mommy.make(Interviewer)
        self.survey_allocation = mommy.make(SurveyAllocation, survey=self.survey,
                                            allocation_ea=self.ea, interviewer=self.interviewer)
        self.access_channel = mommy.make(ODKAccess, interviewer=self.interviewer)
        # create listing questions
        self._create_ussd_non_group_questions()
        self.assertTrue(self.qset.questions.count())
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client = Client()
        self.client.login(username='demo12', password='demo12')

    def _test_create_sampling_criteria(self):
        self.assertEquals(Survey.objects.count(), 1)
        survey = self.survey
        sampling_criteria_url = reverse('listing_criteria_page', args=(survey.id,))
        form_data = {'survey': survey.id, 'validation_test': 'between',
                     'min': 1, 'max': 10, 'listing_question': self.qset.questions.first().id, }
        initial_count = survey.randomization_criteria.count()     # confirm nothin exists
        response = self.client.post(sampling_criteria_url, data=form_data)
        self.assertRedirects(response, sampling_criteria_url, status_code=302,
                             target_status_code=200, msg_prefix='')
        self.assertEquals(survey.randomization_criteria.count(), initial_count + 1)    # confirm one criteria created
        randomization_criteria = survey.randomization_criteria.last()
        self.assertEquals(len(randomization_criteria.test_params), 2)
        for param in randomization_criteria.test_params:
            self.assertIn(int(param), [1, 10])
        # test params display
        self.assertEquals(len(randomization_criteria.params_display()), 2)
        for param in randomization_criteria.params_display():
            self.assertIn(int(param), [1, 10])

    def _test_create_sampling_criteria_with_multichoice(self):
        self.assertEquals(Survey.objects.count(), 1)
        survey = self.survey
        sampling_criteria_url = reverse('listing_criteria_page', args=(survey.id,))
        listing_question = self.qset.questions.filter(answer_type=MultiChoiceAnswer.choice_name()).first()
        form_data = {'survey': survey.id, 'validation_test': 'equals',
                     'options': listing_question.options.first().text,
                     'value': listing_question.options.first().text,
                     'listing_question': listing_question.id, }
        initial_count = survey.randomization_criteria.count()
        response = self.client.post(sampling_criteria_url, data=form_data)
        self.assertRedirects(response, sampling_criteria_url, status_code=302,
                             target_status_code=200, msg_prefix='')
        self.assertEquals(survey.randomization_criteria.count(), initial_count + 1)   # confirm one criteria created
        randomization_criteria = survey.randomization_criteria.last()
        # test params display
        self.assertEquals(len(randomization_criteria.params_display()), 1)
        for param in randomization_criteria.params_display():
            self.assertTrue(param, [listing_question.options.first().text, ])

    def test_create_listing_sample(self):
        # create two conditions
        self._test_create_sampling_criteria()
        self._test_create_sampling_criteria_with_multichoice()
        # now answers to test listing sample
        listing_question = self.qset.questions.filter(answer_type=MultiChoiceAnswer.choice_name()).first()
        n_quest = Question.objects.get(answer_type=NumericalAnswer.choice_name())
        t_quest = Question.objects.get(answer_type=TextAnswer.choice_name())
        m_quest = Question.objects.get(answer_type=MultiChoiceAnswer.choice_name())
        first_option = listing_question.options.first().text
        second_option = listing_question.options.last().text
        # first is numeric, then text, then multichioice
        answers = [{n_quest.id: 1, t_quest.id: 'Hey Man', m_quest.id: first_option},
                   {n_quest.id: 5, t_quest.id: 'Hey Boy', m_quest.id: second_option},
                   {n_quest.id: 15, m_quest.id: first_option},
                   {n_quest.id: 18, t_quest.id: 'Hey Part!'},
                   {n_quest.id: 12, t_quest.id: 'Hey Gerry!', m_quest.id: first_option},
                   {n_quest.id: 10, t_quest.id: 'Hey My guy!', m_quest.id: second_option},
                   {n_quest.id: 17, t_quest.id: 'Hey my Girl!', m_quest.id: second_option},
                   {n_quest.id: 6, m_quest.id: first_option},
                   {n_quest.id: 133,  m_quest.id: first_option},
                   {n_quest.id: 4, m_quest.id: first_option},
                   {n_quest.id: 9,  m_quest.id: first_option},
                   ]
        question_map = {n_quest.id: n_quest, t_quest.id: t_quest, m_quest.id: m_quest}
        Interview.save_answers(self.qset, self.survey, self.ea,
                               self.access_channel, question_map, answers)
        survey = self.survey
        self.assertEquals(Interview.objects.count(), len(answers))
        ListingSample.get_or_create_samples(survey, self.ea)
        # This should create samples with interviews where numeric answers are btween 1 and 10
        self.assertEquals(ListingSample.objects.count(), survey.sample_size)
        for sample in ListingSample.objects.all():
            answers = sample.interview.answer.all()
            self.assertTrue(int(answers.get(question__id=n_quest.id).as_value) >= 1)    # from first criteria creation
            self.assertTrue(int(answers.get(question__id=n_quest.id).as_value) < 10)    # from second criteria creation
            self.assertTrue(answers.get(question__id=m_quest.id).as_text.upper(), first_option.upper())
            # since we did not define any random_sample_label for the survey
            # and since the questonset is not empty, the label should be the very first question
            self.assertEquals(sample.interview.answer.first().as_text, sample.get_display_label())
        # now test the case where some questions have no response for the random label
        self.survey.random_sample_label = '{{%s}}' % t_quest.identifier
        self.survey.save()
        self.survey.refresh_from_db()
        for sample in ListingSample.samples(self.survey, self.ea):
            answers = sample.interview.answer.all()
            first_text = sample.interview.answer.first().as_text
            try:
                expected_label = '%s' % answers.get(question__id=t_quest.id).as_text
            except Answer.DoesNotExist:
                expected_label = '%s' % first_text
            self.assertEquals(string.capwords(expected_label), sample.get_display_label())
            self.assertEquals(get_sample_data_display(sample), sample.get_display_label())


    def test_create_randomization_criteria_with_bad_validation_test(self):
        m_question = self.qset.questions.filter(answer_type=MultiChoiceAnswer.choice_name()).first()
        criteria = RandomizationCriterion.objects.create(listing_question=m_question, validation_test='less_than',
                                                         survey=self.survey)
        self.assertRaises(ValueError, criteria.passes_test, 'Y')


class ListingFormTest(BaseTest):

    def test_listing_form_name(self):
        self.assertFalse(ListingTemplate.verbose_name() is None)