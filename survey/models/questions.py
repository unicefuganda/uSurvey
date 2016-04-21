import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from survey.models.interviews import Answer, MultiChoiceAnswer, MultiSelectAnswer
from survey.models.householdgroups import HouseholdMemberGroup
from survey.models.access_channels import USSDAccess
from survey.models.base import BaseModel
from survey.models.households import Household
from mptt.models import MPTTModel, TreeForeignKey
from model_utils.managers import InheritanceManager
from collections import OrderedDict
from ordered_set import OrderedSet


class Question(BaseModel):
    ANSWER_TYPES = [(name, name) for name in Answer.answer_types()]
    identifier = models.CharField(max_length=100, blank=False, null=True, verbose_name='Variable Name')
    text = models.CharField(max_length=150, blank=False, null=False,
                            #help_text="To replace the household member's name \
        #in the question, please include the variable FAMILY_NAME in curly brackets, e.g. {{ FAMILY_NAME }}. "
                            )
    answer_type = models.CharField(max_length=100, blank=False, null=False, choices=ANSWER_TYPES)
    group = models.ForeignKey(HouseholdMemberGroup, related_name='questions')
    batch = models.ForeignKey('Batch', related_name='batch_questions')
    module = models.ForeignKey("QuestionModule", related_name="questions", default='')

    class Meta:
        app_label = 'survey'        
        unique_together = [('identifier', 'batch'), ]

    def is_loop_start(self):
        from survey.forms.logic import LogicForm
        return self.connecting_flows.filter(desc=LogicForm.BACK_TO_ACTION).exists() #actually the more correct way is to
                                                                 # check if the next is previous

    def is_loop_end(self):
        from survey.forms.logic import LogicForm
        return self.flows.filter(desc=LogicForm.BACK_TO_ACTION).exists() #actually the more correct way is
                                                                        #to check if connecting quest is asked after

    @property
    def loop_ender(self):
        try:
            from survey.forms.logic import LogicForm
            return self.connecting_flows.get(desc=LogicForm.BACK_TO_ACTION).question
        except QuestionFlow.DoesNotExist:
            inlines = self.batch.questions_inline()


    @property
    def looper_flow(self):
        return self.batch.get_looper_flow(self)

    # def loop_inlines(self):


    def delete(self, using=None):
        '''
        Delete related answers before deleting this object
        :param using:
        :return:
        '''
        answer_class = Answer.get_class(self.answer_type)
        answer_class.objects.filter(question=self).delete()
        return super(Question, self).delete(using=using)

    def display_text(self, channel=None):
        text = self.text
        if channel and channel== USSDAccess.choice_name() and self.answer_type == MultiChoiceAnswer.choice_name():
            extras = []
            #append question options
            for option in self.options.all().order_by('order'):
                extras.append(option.to_text)
            text = '%s\n%s' % (text, '\n'.join(extras))
        return text

    def next_question(self, reply):
        flows = self.flows.all()
        answer_class = Answer.get_class(self.answer_type)
        resulting_flow = None
        for flow in flows:
            if flow.validation_test:
                test_values = [arg.param for arg in flow.text_arguments]
                if getattr(answer_class, flow.validation_test)(reply, *test_values) == True:
                    resulting_flow = flow
                    break
            else:
                resulting_flow = flow
        if resulting_flow:
            return resulting_flow.next_question

    def previous_inlines(self):
        inlines = self.batch.questions_inline()
        if self not in inlines:
            raise ValidationError('%s not inline' % self.identifier)
        previous = []
        for q in inlines:
            if q.identifier == self.identifier:
                break
            else:
                previous.append(q)
        return set(previous)

    def direct_sub_questions(self):
        from survey.forms.logic import LogicForm
        sub_flows = self.flows.filter(desc=LogicForm.SUBQUESTION_ACTION, validation_test__isnull=False)
        return OrderedSet([flow.question for flow in sub_flows])
    
    def conditional_flows(self):
        return self.flows.filter( validation_test__isnull=False)
    
    def preceeding_conditional_flows(self):
        return self.connecting_flows.filter( validation_test__isnull=False)

    def __unicode__(self):
        return "%s - %s: (%s)" % (self.identifier, self.text, self.answer_type.upper())
    
    def save(self, *args, **kwargs):
        if self.answer_type not in [MultiChoiceAnswer.choice_name(), MultiSelectAnswer.choice_name()]:
            self.options.all().delete()
        return super(Question, self).save(*args, **kwargs)
    
    @classmethod
    def zombies(cls,  batch):
        #these are the batch questions that do not belong to any flow in any way
        survey_questions = batch.survey_questions
        return batch.batch_questions.exclude(pk__in=[q.pk for q in survey_questions])

    def hierarchical_result_for(self, location_parent, survey):
        locations = location_parent.get_children().order_by('name')[:10]
        answers = self.multichoiceanswer.all()
        return self._format_answer(locations, answers, survey)

    def _format_answer(self, locations, answers, survey):
        question_options = self.options.all()
        data = OrderedDict()
        for location in locations:
            households = Household.all_households_in(location, survey)
            data[location] = {option.text: answers.filter(value=option, interview__householdmember__household__in=households).count() for option in
                              question_options}
        return data
        
    
class QuestionFlow(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__) for validator in Answer.validators()]
    question = models.ForeignKey(Question, related_name='flows')
    validation_test = models.CharField(max_length=200, null=True, blank=True, choices=VALIDATION_TESTS)    
    name = models.CharField(max_length=200, null=True, blank=True) #if validation passes, classify this flow response as having this value
    desc = models.CharField(max_length=200, null=True, blank=True) #this would provide a brief description of this flow
    next_question = models.ForeignKey(Question, related_name='connecting_flows', null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        app_label = 'survey'        
        # unique_together = [('question', 'next_question', 'desc', ),]

    @property
    def test_params(self):
        return [t.param for t in self.text_arguments]

    def params_display(self):
        params = []
        for arg in self.text_arguments:
            if self.question.answer_type == MultiChoiceAnswer.choice_name():
                params.append(self.question.options.get(order=arg.param).text)
            else:
                params.append(arg.param)

        return params

    @property
    def text_arguments(self):
        return TextArgument.objects.filter(flow=self).order_by('position')

    @property
    def test_arguments(self):
        return TestArgument.objects.filter(flow=self).select_subclasses().order_by('position')
    
    def save(self, *args, **kwargs):
        # if self.name is None:
        #     if self.next_question:
        #         identifier = self.next_question.identifier
        #     else: identifier = ''
        #     self.name = "%s %s %s" % (self.question.identifier, self.validation_test or "", identifier)
        return super(QuestionFlow, self).save(*args, **kwargs)


class TestArgument(models.Model):
    objects = InheritanceManager()
    flow = models.ForeignKey(QuestionFlow, related_name='"%(class)s"')
    position = models.PositiveIntegerField()
    
    @classmethod
    def argument_types(cls):
        return [cl.__name__ for cl in cls.__subclasses__()]

    def __unicode__(self):
        return self.param
    
    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'

class TextArgument(TestArgument):
    param = models.TextField()
        
    class Meta:
        app_label = 'survey'

class NumberArgument(TestArgument):
    param = models.IntegerField()
        
    class Meta:
        app_label = 'survey'

class DateArgument(TestArgument):
    param = models.DateField()
        
    class Meta:
        app_label = 'survey'

class QuestionOption(BaseModel):
    question = models.ForeignKey(Question, null=True, related_name="options")
    text = models.CharField(max_length=150, blank=False, null=False)
    order = models.PositiveIntegerField()
 
    class Meta:
        app_label = 'survey'
        ordering = ['order', ]

    @property
    def to_text(self):
        return "%d: %s" % (self.order, self.text)

    def __unicode__(self):
        return self.text
