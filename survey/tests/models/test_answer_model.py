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
from .survey_base_test import SurveyBaseTest


class AnswersTest(SurveyBaseTest):

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
        self.assertEquals(multichoice_answer.as_text.lower(), options.first().text.lower())
        self.assertEquals(int(multichoice_answer.as_value), options.first().order)
        # confirm using value instead yields ame result
        MultiChoiceAnswer.create(self.interview, multichoice_question, options.first().order)
        self.assertEquals(MultiChoiceAnswer.objects.count(), 2)
        multichoice_answer = MultiChoiceAnswer.objects.last()
        self.assertEquals(multichoice_answer.as_text.lower(), options.first().text.lower())
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
        self.assertEquals(Answer.prep_value(answer).lower(), answer.lower())
        self.assertEquals(Answer.prep_text(answer).lower(), answer.lower())
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

    def test_fetch_methods(self):
        qset = self.qset
        self._create_test_non_group_questions(qset)
        date_question = Question.objects.filter(answer_type=DateAnswer.choice_name()).first()
        smallest = '2017-01-20'
        medium = '2017-05-12'
        largest = '2017-10-20'
        answer1 = DateAnswer.create(self.interview, date_question, medium)
        answer2 = DateAnswer.create(self.interview, date_question, smallest)
        answer3 = DateAnswer.create(self.interview, date_question, largest)
        self.assertEquals(DateAnswer.fetch_greater_than('as_value',
                                                        '2017-01-21').filter(as_text__in=[medium, largest]).count(), 2)
        self.assertEquals(DateAnswer.fetch_less_than('as_value', '2017-01-21').count(), 1)
        self.assertEquals(DateAnswer.fetch_less_than('as_value', '2017-01-21').first().as_text, smallest)
        fetched_inbetween = DateAnswer.fetch_between('as_value', '2017-01-21', '2017-05-13')
        self.assertEquals(fetched_inbetween.count(), 1)
        self.assertEquals(fetched_inbetween.first().as_text, medium)
        fetched_inbetween = DateAnswer.fetch_between('as_value', '2017-01-21', '2017-05-13')
        self.assertEquals(fetched_inbetween.count(), 1)
        self.assertEquals(fetched_inbetween.first().as_text, medium)
        self.assertEquals(DateAnswer.fetch_equals('as_value', medium).count(), 1)
        self.assertEquals(DateAnswer.fetch_equals('as_value', medium).first().as_text, medium)
        # check answers attribute is date class
        date_question = Question.objects.filter(answer_type=DateAnswer.choice_name()).first()
        self.assertEquals(date_question.answers().first().__class__, DateAnswer)








