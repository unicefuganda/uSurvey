from survey.models import *

survey = Survey.objects.create(name='MICS Uganda 2013', description='MICS Uganda 2013')
batch = Batch.objects.create(survey=survey, order=2, name="Batch B")

indicator = Indicator.objects.create(batch=batch, order=1, identifier="MN17")
question_1 = Question.objects.create(indicator=indicator, text="How many women aged between 15-49 years are in this household?", answer_type=Question.NUMBER, order=1)
question_2 = Question.objects.create(indicator=indicator, text="How many of these women has had a live birth in the last 2 years?", answer_type=Question.NUMBER, order=2)

indicator = Indicator.objects.create(batch=batch, order=2, identifier="MN18")
question_3 = Question.objects.create(indicator=indicator, text="How many of these child births were delivered in a health facility?", answer_type=Question.NUMBER, order=1)
question_4 = Question.objects.create(indicator=indicator, text="How many of these child births were assisted by a skilled health personnel?", answer_type=Question.NUMBER, order=2)

indicator = Indicator.objects.create(batch=batch, order=3, identifier="MN25")
question_5 = Question.objects.create(indicator=indicator, text="How many of these new borns were breast fed within 1 hour of birth?", answer_type=Question.NUMBER, order=1)


# Rules
AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'], condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0)

AnswerRule.objects.create(question=question_2, action=AnswerRule.ACTIONS['REANSWER'], condition=AnswerRule.CONDITIONS['GREATER_THAN_QUESTION'], validate_with_question=question_1)

AnswerRule.objects.create(question=question_3, action=AnswerRule.ACTIONS['REANSWER'], condition=AnswerRule.CONDITIONS['GREATER_THAN_QUESTION'], validate_with_question=question_2)

AnswerRule.objects.create(question=question_4, action=AnswerRule.ACTIONS['REANSWER'], condition=AnswerRule.CONDITIONS['GREATER_THAN_QUESTION'], validate_with_question=question_2)

AnswerRule.objects.create(question=question_5, action=AnswerRule.ACTIONS['REANSWER'], condition=AnswerRule.CONDITIONS['GREATER_THAN_QUESTION'], validate_with_question=question_2)