from survey.models import *

batch = Batch.objects.create(order=2, name="Batch D")

indicator = Indicator.objects.create(batch=batch, order=1, identifier="MN17")
question_1 = Question.objects.create(indicator=indicator, text="How many women aged between 15-49 years are in this household?", answer_type=Question.NUMBER, order=1)

indicator = Indicator.objects.create(batch=batch, order=2, identifier="__")
question_2 = Question.objects.create(indicator=indicator, text="Have you ever heard of an illness called AIDS?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_2, text="Yes", order=1)
QuestionOption.objects.create(question=question_2, text="No", order=2)

indicator = Indicator.objects.create(batch=batch, order=3, identifier="HA27")
question_3 = Question.objects.create(indicator=indicator, text="Do you know of a place where people can go to get tested for the AIDS virus?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_3, text="Yes", order=1)
QuestionOption.objects.create(question=question_3, text="No", order=2)

indicator = Indicator.objects.create(batch=batch, order=4, identifier="__")
question_4 = Question.objects.create(indicator=indicator, text="Have you ever been tested to see if you have the AIDS virus?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_4, text="Yes", order=1)
QuestionOption.objects.create(question=question_4, text="No", order=2)

indicator = Indicator.objects.create(batch=batch, order=5, identifier="__")
question_5 = Question.objects.create(indicator=indicator, text="When was the most recent time you were tested?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_5, text="Less than 12 months ago", order=1)
QuestionOption.objects.create(question=question_5, text="12-23 months ago", order=2)
QuestionOption.objects.create(question=question_5, text="2 or more years ago", order=3)

indicator = Indicator.objects.create(batch=batch, order=6, identifier="HA8")
question_6 = Question.objects.create(indicator=indicator, text="Can the virus that causes AIDS be transmitted from a mother to her baby during pregnancy?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_6, text="Yes", order=1)
QuestionOption.objects.create(question=question_6, text="No", order=2)

question_7 = Question.objects.create(indicator=indicator, text="Can the virus that causes AIDS be transmitted from a mother to her baby during delivery?", answer_type=Question.MULTICHOICE, order=2)
QuestionOption.objects.create(question=question_7, text="Yes", order=1)
QuestionOption.objects.create(question=question_7, text="No", order=2)

question_8 = Question.objects.create(indicator=indicator, text="Can the virus that causes AIDS be transmitted from a mother to her baby by breastfeeding?", answer_type=Question.MULTICHOICE, order=3)
QuestionOption.objects.create(question=question_8, text="Yes", order=1)
QuestionOption.objects.create(question=question_8, text="No", order=2)

indicator = Indicator.objects.create(batch=batch, order=9, identifier="MT2")
question_9 = Question.objects.create(indicator=indicator, text="How often do you read a newspaper or magazine?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_9, text="Almost every day", order=1)
QuestionOption.objects.create(question=question_9, text="At least once a week", order=2)
QuestionOption.objects.create(question=question_9, text="Less than once a week", order=3)
QuestionOption.objects.create(question=question_9, text="Not at all", order=4)

question_10 = Question.objects.create(indicator=indicator, text="How often do you listen to the radio?", answer_type=Question.MULTICHOICE, order=2)
QuestionOption.objects.create(question=question_10, text="Almost every day", order=1)
QuestionOption.objects.create(question=question_10, text="At least once a week", order=2)
QuestionOption.objects.create(question=question_10, text="Less than once a week", order=3)
QuestionOption.objects.create(question=question_10, text="Not at all", order=4)

question_11 = Question.objects.create(indicator=indicator, text="How often do you watch television?", answer_type=Question.MULTICHOICE, order=3)
QuestionOption.objects.create(question=question_11, text="Almost every day", order=1)
QuestionOption.objects.create(question=question_11, text="At least once a week", order=2)
QuestionOption.objects.create(question=question_11, text="Less than once a week", order=3)
QuestionOption.objects.create(question=question_11, text="Not at all", order=4)

# Rules
AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['END_INTERVIEW'], condition=AnswerRule.CONDITIONS['EQUALS'], validate_with_value=0)
