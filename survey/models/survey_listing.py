__author__ = 'anthony <>'
import random
from django.db import models
from django.db import transaction
from survey.models.base import BaseModel
from survey.models.questions import Question, QuestionSet
from survey.models.interviews import Answer, MultiChoiceAnswer
from survey.models.surveys import Survey
from survey.models.interviews import Interview


class ListingTemplate(QuestionSet):

    class Meta:
        app_label = 'survey'

    @classmethod
    def verbose_name(cls):
        return 'Listing Form'


class ListingQuestion(Question):

    class Meta:
        app_label = 'survey'


class RandomizationCriterion(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__) for validator in Answer.validators()]
    survey = models.ForeignKey(Survey, related_name='randomization_criteria')
    listing_question = models.ForeignKey(Question, related_name='criteria')
    validation_test = models.CharField(max_length=200, choices=VALIDATION_TESTS,null=True, blank=True)

    class Meta:
        app_label = 'survey'

    @property
    def test_params(self):
        return [t.param for t in self.text_arguments]

    @property
    def text_arguments(self):
        return self.arguments.all()

    def params_display(self):
        params = []
        for arg in self.text_arguments:
            if self.question.answer_type == MultiChoiceAnswer.choice_name():
                params.append(self.question.options.get(order=arg.param).text)
            else:
                params.append(arg.param)

        return params

    def passes_test(self, value):
        answer_class = Answer.get_class(self.listing_question.answer_type)
        method = getattr(answer_class, self.validation_test, None)
        if method is None:
            raise ValueError('unsupported validator defined on listing question')
        return method(value, *self.test_params)

    def qs_passes_test(self, value_key, queryset):
        answer_class = Answer.get_class(self.listing_question.answer_type)
        method = getattr(answer_class, 'fetch_%s' % self.validation_test, None)
        return method(value_key, *self.test_params, qs=queryset)

    @property
    def test_arguments(self):
        return CriterionTestArgument.objects.filter(test_condition=self).values_list('param',
                                                                                     flat=True).order_by('position')


class CriterionTestArgument(BaseModel):
    test_condition = models.ForeignKey(RandomizationCriterion, related_name='arguments')
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'


class ListingSample(BaseModel):
    survey = models.ForeignKey(Survey, related_name='listing_samples', db_index=True)
    interview = models.ForeignKey(Interview, related_name='listing_samples')

    @classmethod
    def samples(cls, survey, ea):
        return cls.objects.filter(survey=survey, interview__ea=ea)

    class SamplesAlreadyGenerated(Exception):    # just used to indicated generate random samples has already run
        pass

    @classmethod
    def generate_random_samples(cls, from_survey, to_survey, ea):
        """ Used to generate random samples from listing conducted by from_survey to be used by to_survey
        to do: optimize this method queries
        :param from_survey: Survey from which listing was done
        :param to_survey: Survey for whom the random sample is being generated.
        :param ea: the EA where the survey was conducted
        :return: None
        """
        if cls.samples(to_survey, ea).exists():
            raise cls.SamplesAlreadyGenerated('Samples already generated')

        if to_survey.has_sampling is False or from_survey.has_sampling is False:
            raise ValueError('Either source or destination survey does not support sampling')
        valid_interviews = from_survey.interviews.filter(ea=ea,     # the listed interviews in the ea
                                                         question_set=from_survey.listing_form).values_list('id',
                                                                                                            flat=True)
        #valid_interviews = set(valid_interviews)
        # now get the interviews that meet the randomization criteria
        for criterion in to_survey.randomization_criteria.all():  # need to optimize this
            answer_type = criterion.listing_question.answer_type
            if answer_type == MultiChoiceAnswer.choice_name():
                value_key = 'value__text'
            else:
                value_key = 'value'
            answer_class = Answer.get_class(answer_type)
            kwargs = {
                'question': criterion.listing_question,
                'interview__id__in': valid_interviews,
            }
            #if qs:
            # kwargs['interview__id__in'] = valid_interviews
            valid_interviews = criterion.qs_passes_test(value_key, answer_class.objects.filter(**kwargs).
                                                        only('interview__id').values_list('interview__id', flat=True))
        valid_interviews = list(valid_interviews)
        random.shuffle(valid_interviews)
        random_samples = valid_interviews[:to_survey.sample_size]
        samples = []
        for interview_id in random_samples:
            samples.append(ListingSample(survey=to_survey, interview_id=interview_id))
        with transaction.atomic():
            ListingSample.objects.bulk_create(samples)
