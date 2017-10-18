import string
from model_mommy import mommy
from datetime import datetime
from django_rq import job
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil.parser import parse as extract_date
from django.conf import settings
from survey.models import (InterviewerAccess, ODKAccess, USSDAccess, Interview, Interviewer, QuestionSetChannel,
                           EnumerationArea, Survey, SurveyAllocation, Question, QuestionSet, Batch, BatchQuestion,
                           QuestionOption)
from survey.forms.question import get_question_form
# import all question types
from survey.models import (Answer, NumericalAnswer, TextAnswer, MultiChoiceAnswer, MultiSelectAnswer, GeopointAnswer,
                           ImageAnswer, AudioAnswer, VideoAnswer, DateAnswer, AutoResponse)
from survey.utils.decorators import static_var
from survey.tests.base_test import BaseTest
from survey.forms.answer import SurveyAllocationForm, AddMoreLoopForm


class InterviewsTest(BaseTest):
    fixtures = ['enumeration_area', 'locations', 'location_types']

    def setUp(self):
        self.ea = EnumerationArea.objects.first()
        self.survey = mommy.make(Survey, has_sampling=False)        # just focus on non sampled survey here
        self.interviewer = mommy.make(Interviewer)
        self.survey_allocation = mommy.make(SurveyAllocation, survey=self.survey,
                                            allocation_ea=self.ea, interviewer=self.interviewer)
        self.qset = mommy.make(Batch, name='Test', survey=self.survey)
        self.qset1 = mommy.make(Batch, name='Test1', survey=self.survey)
        self.access_channel = mommy.make(ODKAccess, interviewer=self.interviewer)
        # create the access channel
        self.qset_channels = mommy.make(QuestionSetChannel, qset=self.qset, channel=self.access_channel.choice_name())
        self.interview = mommy.make(Interview, interviewer=self.interviewer, survey=self.survey, ea=self.ea,
                                    interview_channel=self.access_channel, question_set=self.qset)

    def _create_ussd_non_group_questions(self, qset):
        # numeric answer
        data = {
            'answer_type': NumericalAnswer.choice_name(),
            'text': 'num text',
            'identifier': 'num_identifier',
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
            'identifier': 'text_identifier',
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Multichoice questions
        data = {
            'answer_type': MultiChoiceAnswer.choice_name(),
            'text': 'multichoice answer text',
            'identifier': 'multi_choice_identifier',
            'qset': qset.id,
            'options': ['Y', 'N']
        }
        self._save_question(qset, data)
        # Auto questions
        data = {
            'answer_type': AutoResponse.choice_name(),
            'text': 'auto answer text',
            'identifier': 'auto_identifier',
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
            'identifier': 'multi_select_identifier',
            'qset': qset.id,
            'options': ['Y', 'N', 'MB']
        }
        self._save_question(qset, data)
        # Date answer
        data = {
            'answer_type': DateAnswer.choice_name(),
            'text': 'date answer text',
            'identifier': 'date_identifier',
            'qset': qset.id,
        }
        self._save_question(qset, data)
        # Geopoint answer
        data = {
            'answer_type': GeopointAnswer.choice_name(),
            'text': 'geo point text',
            'identifier': 'geo_identifier',
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Image answer
        data = {
            'answer_type': ImageAnswer.choice_name(),
            'text': 'image answer text',
            'identifier': 'image_identifier',
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Audio answer
        data = {
            'answer_type': AudioAnswer.choice_name(),
            'text': 'audio answer text',
            'identifier': 'audio_identifier',
            'qset': qset.id
        }
        self._save_question(qset, data)
        # Video answer
        data = {
            'answer_type': VideoAnswer.choice_name(),
            'text': 'video answer text',
            'identifier': 'video_identifier',
            'qset': qset.id
        }
        self._save_question(qset, data)
        self.qset.refresh_from_db()

    def _save_question(self, qset, data):
        current_count = Question.objects.count()
        QuestionForm = get_question_form(BatchQuestion)
        question_form = QuestionForm(qset, data=data)
        question = question_form.save()
        self.assertEquals(Question.objects.count(), current_count + 1)
        return question

    def _create_group_questions(self, qset, group):
        pass

    def test_name(self):
        interview = self.interview
        self.assertEquals(str(interview), '%s: %s' % (interview.id, interview.question_set.name))

    def test_is_closed(self):
        self.assertEquals(self.interview.closure_date is not None, self.interview.is_closed())

    def test_interview_qset_gives_property_maps_to_correct_type(self):
        self.assertEquals(self.qset.id, self.interview.qset.id)
        self.assertEquals(self.qset.__class__, self.interview.qset.__class__)

    def test_interview_is_considered_stared_when_last_question_is_not_none(self):
        self.assertEquals(self.interview.last_question, None)
        self.assertFalse(self.interview.has_started)

    def test_question_text_is_given_when_no_response_is_supplied(self):
        self._create_ussd_non_group_questions(self.qset)
        interview = self.interview
        first_question = interview.question_set.start_question
        # confirm if its the Numerical answer
        self.assertEquals(first_question.answer_type, NumericalAnswer.choice_name())
        # interview has not started
        self.assertEquals(interview.has_started, False)
        self.assertEquals(Answer.objects.count(), 0)
        response = interview.respond()      # first question is numerical
        self.assertEquals(response, first_question.text)

    def test_last_question_is_updated_after_response(self):
        self._create_ussd_non_group_questions(self.qset)
        interview = self.interview
        first_question = interview.question_set.start_question
        # confirm if its the Numerical answer
        self.assertEquals(first_question.answer_type, NumericalAnswer.choice_name())
        response = interview.respond()
        interview.refresh_from_db()
        self.assertEquals(interview.has_started, True)
        self.assertEquals(interview.last_question.id, first_question.id)

    def _validate_response(self, question, answer, interview=None):
        if interview is None:
            interview = self.interview
        answer_count = Answer.objects.count()
        questions = self.qset.flow_questions
        interview.respond(reply=answer, answers_context={})
        interview.refresh_from_db()
        self.assertEquals(Answer.objects.count(), answer_count+1)
        next_question = question.next_question(answer)
        # just confirm text value of this answer was saved
        self.assertTrue(interview.get_answer(question), str(answer))
        question = Question.get(id=question.id)
        # next test is valid
        if questions.index(question) < len(questions) - 1:
            self.assertEquals(next_question.id, questions[questions.index(question)+1].id)
            self.assertEquals(next_question.id, interview.last_question.id)

    def test_interview_response_flow(self):
        self._create_ussd_non_group_questions(self.qset)
        interview = self.interview
        self._try_interview(interview)

    def _try_interview(self, interview):
        first_question = interview.question_set.start_question
        response = interview.respond()      # first question is numerical
        self.assertEquals(response, first_question.text)
        self._validate_response(first_question, 1, interview=interview)      # numerical question
        self._validate_response(self.qset.flow_questions[1], 'Howdy', interview=interview) # text question
        self._validate_response(self.qset.flow_questions[2], 'N', interview=interview) # Multichoice
        # auto response is internally an integer answer only that its generated by code (but outside models)
        self._validate_response(self.qset.flow_questions[3], 1, interview=interview)  # Auto response
        # now assert that the interview is closed.
        self.assertTrue(interview.is_closed())

    def test_interviews_belonging_to_a_survey(self):
        self._create_ussd_non_group_questions(self.qset)
        interview = mommy.make(Interview, interviewer=self.interviewer, survey=self.survey, ea=self.ea,
                               interview_channel=self.access_channel, question_set=self.qset)
        self._try_interview(interview)
        self.assertEquals(Interview.interviews(self.survey).exclude(survey=self.survey).count(), 0)

    def test_interviews_in_a_location(self):
        self._create_ussd_non_group_questions(self.qset)
        location1 = self.ea.locations.first()
        interview = mommy.make(Interview, interviewer=self.interviewer, survey=self.survey, ea=self.ea,
                               interview_channel=self.access_channel, question_set=self.qset)
        self._try_interview(interview)
        interview = mommy.make(Interview, interviewer=self.interviewer, survey=self.survey, ea=self.ea,
                               interview_channel=self.access_channel, question_set=self.qset)
        self._try_interview(interview)
        self.assertEquals(Interview.interviews_in(location1, include_self=True).count(), Interview.objects.count())
        self.assertEquals(Interview.interviews_in(location1, survey=self.survey, include_self=True).count(),
                          Interview.objects.count())
        # test another location doesnt have any interviews
        location2 = EnumerationArea.objects.exclude(locations__in=self.ea.locations.all()).first().locations.first()
        self.assertEquals(Interview.interviews_in(location2, include_self=True).count(), 0)
        self.assertEquals(Interview.interviews_in(location2, survey=self.survey, include_self=True).count(), 0)

    def test_bulk_answer_questions(self):
        self._create_ussd_non_group_questions(self.qset)
        answers = []
        n_quest = Question.objects.get(answer_type=NumericalAnswer.choice_name())
        t_quest = Question.objects.get(answer_type=TextAnswer.choice_name())
        m_quest = Question.objects.get(answer_type=MultiChoiceAnswer.choice_name())
        # first is numeric, then text, then multichioice
        answers = [{n_quest.id: 1, t_quest.id: 'Hey Man', m_quest.id: 'Y'},
                   {n_quest.id: 5, t_quest.id: 'Hey Boy', m_quest.id: 'Y'},
                   {n_quest.id: 15, t_quest.id: 'Hey Girl!', m_quest.id: 'N'},
                   {n_quest.id: 15, t_quest.id: 'Hey Part!'}
                   ]
        question_map = {n_quest.id: n_quest, t_quest.id: t_quest, m_quest.id: m_quest}
        interview = self.interview
        Interview.save_answers(self.qset, self.survey, self.ea,
                               self.access_channel, question_map, answers)
        # confirm that 11 answers has been created
        self.assertEquals(NumericalAnswer.objects.count(), 4)
        self.assertEquals(TextAnswer.objects.count(), 4)
        self.assertEquals(MultiChoiceAnswer.objects.count(), 3)
        self.assertEquals(TextAnswer.objects.first().to_text(), 'Hey Man')
        self.assertEquals(MultiChoiceAnswer.objects.first().to_text(), 'Y')
        self.assertEquals(MultiChoiceAnswer.objects.first().to_label(), str(QuestionOption.objects.get(text='Y').order))




