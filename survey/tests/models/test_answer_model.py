from model_mommy import mommy
from django.core.management import call_command
from django.test import TestCase
from survey.models import (InterviewerAccess, ODKAccess, USSDAccess, Interview, Interviewer, QuestionSetChannel,
                           EnumerationArea, Survey, SurveyAllocation, Question, QuestionSet, Batch, BatchQuestion,
                           QuestionOption)
from survey.forms.question import get_question_form
# import all question types
from survey.models import (Answer, NumericalAnswer, TextAnswer, MultiChoiceAnswer, MultiSelectAnswer, GeopointAnswer,
                           ImageAnswer, AudioAnswer, VideoAnswer, DateAnswer, AutoResponse)


class AnswersTest(TestCase):

    fixtures = ['enumeration_area', 'locations', 'location_types']

    def setUp(self):
        # locad parameters required
        call_command('load_parameters')
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

    def test_answer_types_available(self):
        known_answer_types = [NumericalAnswer, AutoResponse, MultiSelectAnswer, TextAnswer, MultiChoiceAnswer,
                              AudioAnswer, VideoAnswer, ImageAnswer, GeopointAnswer
                              ]
        for answer_type in known_answer_types:
            self.assertIn(answer_type.choice_name(), Answer.answer_types())

    def test_answer_validators(self):
        validators = [                  # supported validators
            'starts_with',
            'ends_with',
            'equals',
            'between',
            'less_than',
            'greater_than',
            'contains',
        ]
        for func in Answer.validators():
            self.assertIn(func.__name__, validators)
        # test Numeric Answer Validators
        validators = [                  # supported validators
            'equals',
            'between',
            'less_than',
            'greater_than',
        ]
        for func in NumericalAnswer.validators():
            self.assertIn(func.__name__, validators)
        # test Text Answer Validators
        validators = [                  # supported validators
            'starts_with',
            'ends_with',
            'equals',
            'contains',
        ]
        for func in TextAnswer.validators():
            self.assertIn(func.__name__, validators)
        # Multichoice
        validators = [                  # supported validators
            'equals',
        ]
        for func in MultiChoiceAnswer.validators():
            self.assertIn(func.__name__, validators)
        # test Multiselect Answer Validators
        validators = [                  # supported validators
            'equals',
            'contains',
        ]
        for func in MultiSelectAnswer.validators():
            self.assertIn(func.__name__, validators)
        # test Date Answer Validators
        validators = [                  # supported validators
            'equals',
            'between',
            'less_than',
            'greater_than',
        ]
        for func in DateAnswer.validators():
            self.assertIn(func.__name__, validators)
        # GeoPoint Answer
        validators = [  # supported validators
            'equals',
        ]
        for func in GeopointAnswer.validators():
            self.assertIn(func.__name__, validators)
        # file answers should return no validators
        for answer_class in [VideoAnswer, AudioAnswer, ImageAnswer]:
            self.assertEquals(len(answer_class.validators()), 0)

    def test_create_answers(self):
        qset = self.qset
        self._create_test_non_group_questions(qset)
        geo_question = Question.objects.filter(answer_type=GeopointAnswer.choice_name()).first()
        latitude = '23.2'
        longitiude = '-30.34'
        altitude = '100'
        precision = '5'
        # Test ODK Geopoint
        GeopointAnswer.create(self.interview, geo_question, ' '.join([latitude, longitiude, altitude, precision]))
        self.assertEquals(GeopointAnswer.objects.count(), 1)

    def test_update_multichoice_answer(self):
        qset = self.qset
        self._create_test_non_group_questions(qset)
        multichoice_question = Question.objects.filter(answer_type=MultiChoiceAnswer.choice_name()).first()
        options = multichoice_question.options.all()
        MultiChoiceAnswer.create(self.interview, multichoice_question, options.first().text)
        self.assertEquals(MultiChoiceAnswer.objects.count(), 1)
        multichoice_answer = MultiChoiceAnswer.objects.first()
        self.assertEquals(multichoice_answer.as_text, options.first().text)
        self.assertEquals(int(multichoice_answer.as_value), options.first().order)
        # confirm using value instead yields ame result
        MultiChoiceAnswer.create(self.interview, multichoice_question, options.first().order)
        self.assertEquals(MultiChoiceAnswer.objects.count(), 2)
        multichoice_answer = MultiChoiceAnswer.objects.last()
        self.assertEquals(multichoice_answer.as_text, options.first().text)
        self.assertEquals(int(multichoice_answer.as_value), options.first().order)
        # confirm update now
        multichoice_answer.update(options.last().text)
        multichoice_answer.refresh_from_db()
        self.assertEquals(int(multichoice_answer.as_value), options.last().order)
        # update back to original option
        multichoice_answer.update(options.first().order)
        multichoice_answer.refresh_from_db()
        self.assertEquals(int(multichoice_answer.as_value), options.first().order)

    def test_update_multiselect_answer(self):
        qset = self.qset
        self._create_test_non_group_questions(qset)
        multiselect_question = Question.objects.filter(answer_type=MultiSelectAnswer.choice_name()).first()
        options = multiselect_question.options.all()
        raw_answer = ' '.join([options.first().text, options.last().text])
        MultiSelectAnswer.create(self.interview, multiselect_question, raw_answer)
        self.assertEquals(MultiSelectAnswer.objects.count(), 1)
        multichoice_answer = MultiSelectAnswer.objects.first()
        self.assertEquals(multichoice_answer.as_text, raw_answer)
        self.assertEquals(multichoice_answer.as_value, raw_answer)
        # not save all options as queryset
        MultiSelectAnswer.create(self.interview, multiselect_question, multiselect_question.options.all())
        self.assertEquals(MultiSelectAnswer.objects.count(), 2)
        multichoice_answer = MultiSelectAnswer.objects.last()
        self.assertEquals(multichoice_answer.as_text,
                          ' '.join(multiselect_question.options.values_list('text', flat=True)))
        self.assertEquals(multichoice_answer.as_value,
                          ' '.join(multiselect_question.options.values_list('text', flat=True)))


    def test_prep_values(self):
        # test base answer. For base answer just return value and text values
        answer = 'Test1'
        self.assertEquals(Answer.prep_value(answer), answer)
        self.assertEquals(Answer.prep_text(answer), answer)
        # test numerial answer. Confirm zfill normalization
        answer = 1
        self.assertEquals(NumericalAnswer.prep_text(answer), str(answer).zfill(NumericalAnswer.STRING_FILL_LENGTH))
        self.assertEquals(NumericalAnswer.prep_value(answer), str(answer).zfill(NumericalAnswer.STRING_FILL_LENGTH))
        # Confirm the auto response verbose_name (sorry I'm just throwing it in here)'
        self.assertEquals(AutoResponse.choice_name(), 'Auto Generated')

    def test_contains(self):
        # test on base class. Just test with text
        answer = 'Say Hey'
        self.assertTrue(Answer.contains(answer, 'hey'))
        self.assertFalse(Answer.contains(answer, 'somethign else'))
        # Test Text
        answer = 'Hey'
        self.assertTrue(TextAnswer.contains(answer, 'hey'))
        self.assertFalse(TextAnswer.contains(answer, 'somethign else'))




