from survey.models import *

batch = Batch.objects.create(order=2, name="Batch E")


question_1 = Question.objects.create(batch=batch, text="Can people reduce their chance of getting the AIDS virus by having just one uninfected sex partner who has no other sex partners?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_1, text="Yes", order=1)
QuestionOption.objects.create(question=question_1, text="No", order=2)
QuestionOption.objects.create(question=question_1, text="Don't know", order=3)

question_2 = Question.objects.create(batch=batch, text="Can people get the AIDS virus because of witchcraft or other supernatural means?", answer_type=Question.MULTICHOICE, order=2)
QuestionOption.objects.create(question=question_2, text="Yes", order=1)
QuestionOption.objects.create(question=question_2, text="No", order=2)
QuestionOption.objects.create(question=question_2, text="Don't know", order=3)

question_3 = Question.objects.create(batch=batch, text="Can people reduce their chance of getting the AIDS virus by using a condom every time they have sex?", answer_type=Question.MULTICHOICE, order=3)
QuestionOption.objects.create(question=question_3, text="Yes", order=1)
QuestionOption.objects.create(question=question_3, text="No", order=2)
QuestionOption.objects.create(question=question_3, text="Don't know", order=3)

question_4 = Question.objects.create(batch=batch, text="Can people get the AIDS virus from mosquito bites?", answer_type=Question.MULTICHOICE, order=4)
QuestionOption.objects.create(question=question_4, text="Yes", order=1)
QuestionOption.objects.create(question=question_4, text="No", order=2)
QuestionOption.objects.create(question=question_4, text="Don't know", order=3)

question_5 = Question.objects.create(batch=batch, text="Can people get the AIDS virus by sharing food with a person who has the AIDS virus?", answer_type=Question.MULTICHOICE, order=5)
QuestionOption.objects.create(question=question_5, text="Yes", order=1)
QuestionOption.objects.create(question=question_5, text="No", order=2)
QuestionOption.objects.create(question=question_5, text="Don't know", order=3)

question_6 = Question.objects.create(batch=batch, text="Is it possible for a healthy-looking person to have the AIDS virus?", answer_type=Question.MULTICHOICE, order=6)
QuestionOption.objects.create(question=question_6, text="Yes", order=1)
QuestionOption.objects.create(question=question_6, text="No", order=2)
QuestionOption.objects.create(question=question_6, text="Don't know", order=3)


question_7 = Question.objects.create(batch=batch, text="In the last 12 months, have you used a computer?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_7, text="Yes", order=1)
QuestionOption.objects.create(question=question_7, text="No", order=2)

question_8 = Question.objects.create(batch=batch, text="During the last one month, how often did you use a computer?", answer_type=Question.MULTICHOICE, order=2)
QuestionOption.objects.create(question=question_8, text="Almost every day", order=1)
QuestionOption.objects.create(question=question_8, text="At least once a week", order=2)
QuestionOption.objects.create(question=question_8, text="Less than once a week", order=3)
QuestionOption.objects.create(question=question_8, text="Not at all", order=4)

question_9 = Question.objects.create(batch=batch, text="In the last 12 months, have you used the internet?", answer_type=Question.MULTICHOICE, order=3)
QuestionOption.objects.create(question=question_9, text="Yes", order=1)
QuestionOption.objects.create(question=question_9, text="No", order=2)

question_10 = Question.objects.create(batch=batch, text="During the last one month, how often did you use the internet?", answer_type=Question.MULTICHOICE, order=4)
QuestionOption.objects.create(question=question_10, text="Almost every day", order=1)
QuestionOption.objects.create(question=question_10, text="At least once a week", order=2)
QuestionOption.objects.create(question=question_10, text="Less than once a week", order=3)
QuestionOption.objects.create(question=question_10, text="Not at all", order=4)


question_11 = Question.objects.create(batch=batch, text="Compared to this time last year, would you say that your life has improved, stayed more or less the same, or worsened, overall?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_11, text="Improved", order=1)
QuestionOption.objects.create(question=question_11, text="More or less the same", order=2)
QuestionOption.objects.create(question=question_11, text="Worsened", order=3)

question_12 = Question.objects.create(batch=batch, text="And in one year from now, do you expect that your life will be better, will be more or less the same, or will be worse, overall?", answer_type=Question.MULTICHOICE, order=2)
QuestionOption.objects.create(question=question_12, text="Better", order=1)
QuestionOption.objects.create(question=question_12, text="More or less the same", order=2)
QuestionOption.objects.create(question=question_12, text="Worsened", order=3)

# Rules
