from survey.models import *

batch = Batch.objects.create(order=2, name="Batch C")


question_1 = Question.objects.create(batch=batch, text="How many times did you receive antenatal care during the last pregnancy?", answer_type=Question.NUMBER, order=1)

question_2 = Question.objects.create(batch=batch, text="During any of these antenatal visits for the pregnancy, how many times did you take medicine to prevent malaria?", answer_type=Question.NUMBER, order=2)


question_3 = Question.objects.create(batch=batch, text="During the last pregnancy, did you receive any injection on the arm or shoulder to prevent the baby from getting tetanus?", answer_type=Question.MULTICHOICE, order=1)
QuestionOption.objects.create(question=question_3, text="Yes", order=1)
no_option = QuestionOption.objects.create(question=question_3, text="No", order=2)

question_4 = Question.objects.create(batch=batch, text="How many times did you receive this tetanus injection during your pregnancy?", answer_type=Question.NUMBER, order=2)

# Rules
AnswerRule.objects.create(question=question_3, action=AnswerRule.ACTIONS['END_INTERVIEW'], condition=AnswerRule.CONDITIONS['EQUALS_OPTION'], validate_with_option=no_option)
