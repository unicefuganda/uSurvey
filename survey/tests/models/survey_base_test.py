from model_mommy import mommy
import random
from django.core.management import call_command
from survey.tests.base_test import BaseTest, Base
from survey.models import (InterviewerAccess, ODKAccess, USSDAccess, Interview, Interviewer, QuestionSetChannel,
                           EnumerationArea, Survey, SurveyAllocation, Question, QuestionSet, Batch, BatchQuestion,
                           QuestionOption)
from survey.forms.question import get_question_form
# import all question types
from survey.models import (Answer, NumericalAnswer, TextAnswer, MultiChoiceAnswer, MultiSelectAnswer, GeopointAnswer,
                           ImageAnswer, AudioAnswer, VideoAnswer, DateAnswer, AutoResponse)


class SurveyBaseTest(BaseTest):
    """Base class to provide implemtors with some basic data/functions for survey to reduce duplicate code"""

    fixtures = ['enumeration_area', 'locations', 'location_types', 'contenttypes', 'groups', 'permissions',
                'answeraccessdefinition.json']

    def setUp(self):
        # locad parameters required
        #
        self.ea = EnumerationArea.objects.first()
        self.survey = mommy.make(Survey, has_sampling=False)        # just focus on non sampled survey here
        self.interviewer = mommy.make(Interviewer)
        self.survey_allocation = mommy.make(SurveyAllocation, survey=self.survey,
                                            allocation_ea=self.ea, interviewer=self.interviewer)
        self.qset = mommy.make(Batch, name='TestQset', survey=self.survey)
        self.qset1 = mommy.make(Batch, name='TestNewQset', survey=self.survey)
        self.access_channel = mommy.make(ODKAccess, interviewer=self.interviewer)
        # create the access channel
        self.qset_channels = mommy.make(QuestionSetChannel, qset=self.qset, channel=self.access_channel.choice_name())
        self.interview = mommy.make(Interview, interviewer=self.interviewer, survey=self.survey, ea=self.ea,
                                    interview_channel=self.access_channel, question_set=self.qset)

    def _create_ussd_non_group_questions(self, qset=None):
        if qset is None:
            qset = self.qset
        # numeric answer
        data = {
            'answer_type': NumericalAnswer.choice_name(),
            'text': 'num text',
            'identifier': 'num1_identifier_%s' % random.randint(1, 100),
            'qset': qset.id
        }
        question = self._save_question(qset, data)
        qset.refresh_from_db()  # qset is updated by question (start_question attribute is updated)
        # since it's the first question saved it must reflect as first question of the question set
        self.assertEquals(qset.start_question.id, question.id)
        # text answer
        data = {
            'answer_type': TextAnswer.choice_name(),
            'text': 'texts text',
            'identifier': 'text1_identifier_%s' % random.randint(1, 100),
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Multichoice questions
        data = {
            'answer_type': MultiChoiceAnswer.choice_name(),
            'text': 'multichoice answer text',
            'identifier': 'multi1_choice_identifier_%s' % random.randint(1, 100),
            'qset': qset.id,
            'options': ['Y', 'N']
        }
        self._save_question(qset, data)
        # Auto questions
        data = {
            'answer_type': AutoResponse.choice_name(),
            'text': 'auto answer text',
            'identifier': 'auto1_identifier_%s' % random.randint(1, 100),
            'qset': qset.id,
        }
        self._save_question(qset, data)
        self.qset.refresh_from_db()

    def _create_test_non_group_questions(self, qset):
        # Basically create questions for this question set which is not having groups
        self._create_ussd_non_group_questions(qset)
        # Multiselect questions
        data = {
            'answer_type': MultiSelectAnswer.choice_name(),
            'text': 'multi select answer text',
            'identifier': 'multi2_select_identifier_%s' % random.randint(1, 100),
            'qset': qset.id,
            'options': ['Y', 'N', 'MB']
        }
        self._save_question(qset, data)
        # Date answer
        data = {
            'answer_type': DateAnswer.choice_name(),
            'text': 'date answer text',
            'identifier': 'date2_identifier_%s' % random.randint(1, 100),
            'qset': qset.id,
        }
        self._save_question(qset, data)
        # Geopoint answer
        data = {
            'answer_type': GeopointAnswer.choice_name(),
            'text': 'geo point text',
            'identifier': 'geo2_identifier_%s' % random.randint(1, 100),
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Image answer
        data = {
            'answer_type': ImageAnswer.choice_name(),
            'text': 'image answer text',
            'identifier': 'image2_identifier_%s' % random.randint(1, 100),
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Audio answer
        data = {
            'answer_type': AudioAnswer.choice_name(),
            'text': 'audio answer text',
            'identifier': 'audio2_identifier_%s' % random.randint(1, 100),
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Video answer
        data = {
            'answer_type': VideoAnswer.choice_name(),
            'text': 'video answer text',
            'identifier': 'video2_identifier_%s' % random.randint(1, 100),
            'qset': qset.id
        }
        self._save_question(qset, data)
        self.qset.refresh_from_db()

    def _save_question(self, qset, data):
        current_count = Question.objects.count()
        QuestionForm = get_question_form(BatchQuestion)
        question_form = QuestionForm(qset, data=data)
        self.assertTrue(question_form.is_valid())
        question = question_form.save()
        self.assertEquals(Question.objects.count(), current_count + 1)
        return question


# class SurveyBaseTest(SurveyBase, BaseTest):
#      pass
