from django.db import models
from survey.models.question import Question, QuestionOption
from survey.models.base import BaseModel

class AnswerRule(BaseModel):
    ACTIONS = {
                'END_INTERVIEW': 'END_INTERVIEW',
                'SKIP_TO': 'SKIP_TO',
                'REANSWER': 'REANSWER',
                'ASK_SUBQUESTION': 'ASK_SUBQUESTION',
    }
    ACTION_METHODS = {
                'END_INTERVIEW': 'end_interview',
                'SKIP_TO': 'skip_to',
                'REANSWER': 'reanswer',
                'ASK_SUBQUESTION': 'ask_subquestion',
    }
    CONDITIONS = {
                'GREATER_THAN_QUESTION': 'GREATER_THAN_QUESTION',
                'GREATER_THAN_VALUE': 'GREATER_THAN_VALUE',
                'EQUALS': 'EQUALS',
                'EQUALS_OPTION': 'EQUALS_OPTION',
                'LESS_THAN_QUESTION': 'LESS_THAN_QUESTION',
                'LESS_THAN_VALUE': 'LESS_THAN_VALUE',
    }
    CONDITION_METHODS = {
                'EQUALS': 'is_equal',
                'EQUALS_OPTION': 'equals_option',
                'GREATER_THAN_QUESTION': 'greater_than_question',
                'GREATER_THAN_VALUE': 'greater_than_value',
                'LESS_THAN_QUESTION': 'less_than_question',
                'LESS_THAN_VALUE': 'less_than_value',
    }

    question = models.ForeignKey(Question, null=True, related_name="rule")
    batch = models.ForeignKey("Batch", null=True, related_name='batch_rule')
    action = models.CharField(max_length=100, blank=False, null=False, choices=ACTIONS.items())
    condition = models.CharField(max_length=100, blank=False, null=False, choices=CONDITIONS.items())
    next_question = models.ForeignKey(Question, null=True, related_name="parent_question_rules")
    validate_with_value = models.PositiveIntegerField(max_length=2, null=True)
    validate_with_question = models.ForeignKey(Question, null=True)
    validate_with_option = models.ForeignKey(QuestionOption, null=True, related_name="answer_rule")

    class Meta:
        app_label = 'survey'


    def is_equal(self, answer):
        return self.validate_with_value == answer.answer

    def equals_option(self, answer):
        return self.validate_with_option == answer.answer

    def greater_than_question(self, answer):
        return answer.answer > answer.investigator.last_answer_for(self.validate_with_question).answer

    def greater_than_value(self, answer):
        return answer.answer > self.validate_with_value

    def less_than_question(self, answer):
        return answer.answer < answer.investigator.last_answer_for(self.validate_with_question).answer

    def less_than_value(self, answer):
        return answer.answer < self.validate_with_value

    def end_interview(self, investigator, answer):
        if answer.rule_applied:
            return None
        if not investigator.can_end_the_interview(self.question):
            investigator.confirm_end_interview(self.question)
            return self.reanswer(investigator, answer)
        else:
            self.rule_applied_to(answer)
            return None

    def rule_applied_to(self, answer):
        answer.rule_applied = self
        answer.save()

    def skip_to(self, investigator, answer):
        return self.next_question

    def reanswer(self, investigator, answer):
        investigator.reanswer(self.question)
        if self.validate_with_question:
            investigator.reanswer(self.validate_with_question)
            return self.validate_with_question
        else:
            return self.question

    def ask_subquestion(self, investigator, answer):
        return self.skip_to(investigator, answer)

    def action_to_take(self, investigator, answer):
        method = getattr(self, self.ACTION_METHODS[self.action])
        return method(investigator, answer)

    def validate(self, answer):
        method = getattr(self, self.CONDITION_METHODS[self.condition])
        return method(answer)