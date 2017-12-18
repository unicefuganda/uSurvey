import string
from model_mommy import mommy
from datetime import datetime
from django.utils import timezone
from django import forms
from dateutil.parser import parse as extract_date
from django.conf import settings
from survey.models import *
from survey.forms.question import get_question_form
from survey.forms.logic import LogicForm
from .survey_base_test import SurveyBaseTest
from survey.tests.base_test import BaseTest


class QuestionModelTest(SurveyBaseTest):

    def setUp(self):
        super(QuestionModelTest, self).setUp()
        self.listing_form = mommy.make(ListingTemplate)
        self.listing_question = mommy.make(Question, qset=self.listing_form)
        self.sampling_survey = mommy.make(Survey, listing_form=self.listing_form, has_sampling=True, name='sample test survey')
        self.batch = mommy.make(Batch, survey=self.sampling_survey)
        # self.parameter_question =

    def test_get_question_brings_correct_question_type(self):
        self.assertEquals(QuestionSet.get(pk=self.batch.pk).__class__, Batch)

    def test_save_loop_always_require_numeric_in_previous_question_count(self):
        q1 = BatchQuestion.objects.create(qset=self.batch, identifier='test1',
                                          text='test1', answer_type=NumericalAnswer.choice_name())
        q2 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1,
                                          identifier='test2', text='test2', answer_type=TextAnswer.choice_name())
        q3 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test3',
                                          text='test3', answer_type=NumericalAnswer.choice_name())
        q4 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test45',
                                          text='test45', answer_type=NumericalAnswer.choice_name())
        q5 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test5',
                                          text='test5', answer_type=NumericalAnswer.choice_name())
        self.batch.start_question = q1
        self.batch.save()
        data = {
            'loop_starter': q3,
            'loop_ender': q5,
            'repeat_logic': QuestionLoop.PREVIOUS_QUESTION,
        }
        loop = mommy.make(QuestionLoop, **data)
        p = PreviousAnswerCount(loop=loop, value=q2)
        self.assertRaises(forms.ValidationError, p.save)
        p = PreviousAnswerCount(loop=loop, value=q1)
        p.save()
        self.assertTrue(PreviousAnswerCount.objects.exists())

    def test_inlines_between(self):
        self._create_ussd_non_group_questions()
        all_questions = self.qset.all_questions
        between = self.qset.inlines_between(all_questions[0], all_questions[-1])
        between = [q.id for q in between]
        # self.assertNotIn(all_questions[0].id, between)
        self.assertNotIn(all_questions[-1].id, between)
        for question in all_questions[:-1]:
            self.assertIn(question.id, between)

    def test_clone_qset(self):
        self._create_ussd_non_group_questions()
        self.qset.name = 'something good'
        self.qset.save()
        all_questions = self.qset.all_questions
        validation = mommy.make(ResponseValidation, validation_test='greater_than')
        mommy.make(TextArgument, validation=validation, position=1, param=23)
        question = mommy.make(Question, qset=self.qset, answer_type=NumericalAnswer.choice_name())
        mommy.make(QuestionFlow, question=all_questions[1], next_question=question,
                   validation=validation)
        cloned_batch = self.qset.deep_clone()
        all_questions1 = cloned_batch.all_questions
        all_questions2 = self.qset.all_questions
        for idx, question in enumerate(all_questions1):
            self.assertEquals(all_questions1[idx].identifier, all_questions2[idx].identifier)

    def test_inline_flow(self):
        self._create_ussd_non_group_questions()
        all_questions = self.qset.all_questions
        self.assertEquals(len(all_questions[0].flows.first().test_arguments), 0)










