__author__ = 'anthony <>'
from django.db import models
from survey.models.base import BaseModel
from survey.models.generics import TemplateQuestion
from survey.models.questions import Question, QuestionSet, QuestionOption, QuestionFlow
from survey.models.interviews import Answer
from survey.models.interviews import MultiChoiceAnswer


class ParameterTemplate(TemplateQuestion):

    class Meta:
        app_label = 'survey'

    def __unicode__(self):
        return self.identifier


class RespondentGroup(BaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def has_interviews(self):
        from survey.models import Interview
        return self.questions.exists() and \
               Interview.objects.filter(question_set__pk=self.questions.first().qset.pk).exists()

    def remove_related_questions(self):
        self.question_templates.all().delete()

    def __unicode__(self):
        return self.name


class RespondentGroupCondition(BaseModel):
    VALIDATION_TESTS = [(validator.__name__, validator.__name__)
                        for validator in Answer.validators()]
    respondent_group = models.ForeignKey(RespondentGroup, related_name='group_conditions')
    test_question = models.ForeignKey(ParameterTemplate, related_name='group_condition')
    validation_test = models.CharField(
        max_length=200, null=True, blank=True, choices=VALIDATION_TESTS)

    class Meta:
        app_label = 'survey'

    @property
    def test_params(self):
        return [t.param for t in self.test_arguments]

    def params_display(self):
        params = []
        for arg in self.text_arguments:
            if self.question.answer_type == MultiChoiceAnswer.choice_name():
                params.append(self.question.options.get(order=arg.param).text)
            else:
                params.append(arg.param)
        return params

    @property
    def test_arguments(self):
        return GroupTestArgument.objects.filter(group_condition=self).order_by('position')


class GroupTestArgument(BaseModel):
    group_condition = models.ForeignKey(RespondentGroupCondition, related_name='arguments')
    position = models.PositiveIntegerField()
    param = models.CharField(max_length=100)

    def __unicode__(self):
        return self.param

    class Meta:
        app_label = 'survey'
        get_latest_by = 'position'


class ParameterQuestion(Question):

    def next_question(self, reply):
        next_question = super(ParameterQuestion, self).next_question(reply)
        if next_question is None and self.e_qset.batch:
            next_question = self.e_qset.batch.start_question
        return next_question


class SurveyParameterList(QuestionSet):             # basically used to tag survey grouping questions
    batch = models.OneToOneField('Batch', related_name='parameter_list', null=True, blank=True)

    @property
    def parameters(self):
        return ParameterQuestion.objects.filter(qset=self)

    class Meta:
        app_label = 'survey'

    @classmethod
    def update_parameter_list(cls, batch):
        """Updates the parameter list for this batch.
        Basically checks all the groups registered in this batch and ensures required parameter list is updated.
        Presently because the entire group parameters required in a batch would typically be less than 10, The strategy
         employed here shall be to delete all parameters and create new when called.
         Questions in returned question set does not necessarily belong to any flow.
        :param batch:
        :return:
        """
        param_list, _ = cls.objects.get_or_create(batch=batch)
        param_list.questions.all().delete()
        # now create a new
        groups = RespondentGroup.objects.filter(questions__qset=batch)
        question_ids = []
        # loop through groups to get required template parameters
        for group in groups:
            map(lambda condition: question_ids.append(condition.test_question.id), group.group_conditions.all())
        parameters = ParameterTemplate.objects.filter(id__in=question_ids).order_by('identifier')
        prev_question = None
        for param in parameters:
            # going this route because param questions typically would be small
            question = ParameterQuestion(**{'identifier': param.identifier, 'text': param.text,
                                            'answer_type': param.answer_type, 'qset': param_list})
            question.save()
            if prev_question:
                QuestionFlow.objects.create(question=prev_question, next_question=question)
            prev_question = question
            if question.answer_type in [MultiChoiceAnswer.choice_name(), MultiChoiceAnswer]:
                for option in param.options.all():
                    QuestionOption.objects.create(order=option.order, text=option.text, question=question)
        return param_list




# class SurveyParameter(Question):        # this essentially shall be made from copying from survey paramaters.
#     pass                            # It is required to
