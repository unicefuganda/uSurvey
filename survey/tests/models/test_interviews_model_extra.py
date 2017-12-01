import string
from model_mommy import mommy
from datetime import datetime
from django_rq import job
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil.parser import parse as extract_date
from django.conf import settings
from survey.models import *
from survey.utils.decorators import static_var
from survey.tests.base_test import BaseTest
from survey.forms.answer import SurveyAllocationForm, AddMoreLoopForm
from .survey_base_test import SurveyBaseTest


class InterviewsTest(SurveyBaseTest):

    def test_get_answer_with_question_not_yet_answered(self):
        self._create_ussd_non_group_questions()
        num_question = Question.objects.filter(answer_type=NumericalAnswer.choice_name()).last()
        self.assertEquals(self.interview.get_answer(num_question), '')

    def test_save_answers_with_interview_id(self):
        self._create_ussd_non_group_questions(self.qset)
        answers = []
        n_quest = Question.objects.get(answer_type=NumericalAnswer.choice_name())
        t_quest = Question.objects.get(answer_type=TextAnswer.choice_name())
        m_quest = Question.objects.get(answer_type=MultiChoiceAnswer.choice_name())
        answers = [{n_quest.id: 1, t_quest.id: 'Hey Man', m_quest.id: 'Y'},
                   {n_quest.id: 5, t_quest.id: 'Hey Boy', m_quest.id: 'Y'},
                   {n_quest.id: 15, t_quest.id: 'Hey Girl!', m_quest.id: 'N'},
                   {n_quest.id: 15, t_quest.id: 'Hey Part!'}
                   ]
        question_map = {n_quest.id: n_quest, t_quest.id: t_quest, m_quest.id: m_quest}
        Interview.save_answers(self.qset, self.survey, self.ea,
                               self.access_channel, question_map, answers, reference_interview=self.interview.id)
        self.assertEquals(NumericalAnswer.objects.count(), 4)
        self.assertEquals(TextAnswer.objects.count(), 4)
        self.assertEquals(MultiChoiceAnswer.objects.count(), 3)
        self.assertEquals(TextAnswer.objects.first().to_text().lower(), 'Hey Man'.lower())
        self.assertEquals(MultiChoiceAnswer.objects.first().as_text.lower(), 'Y'.lower())
        self.assertEquals(MultiChoiceAnswer.objects.first().as_value, str(QuestionOption.objects.get(text='Y').order))
        self.assertEquals(Interview.objects.last().interview_reference, self.interview)

    def test_interview_with_survey_parameters(self):
        # self._create_ussd_group_questions()
        pass