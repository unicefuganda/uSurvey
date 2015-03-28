from survey.models import BaseModel, Question, Batch
from django.db import models


class BatchQuestionOrder(BaseModel):
    question = models.ForeignKey(Question, related_name="question_batch_order")
    batch = models.ForeignKey(Batch, related_name="batch_question_order")
    order = models.PositiveIntegerField(null=False)

    @classmethod
    def next_question_order_for(cls, batch):
        all_batches = BatchQuestionOrder.objects.select_related('batch').filter(batch=batch).order_by('-order')
        return (all_batches[0].order + 1) if all_batches.exists() else 1

    @classmethod
    def update_question_order(cls, new_order, batch):
        order_question_id = str(new_order).split('-')
        question = Question.objects.get(id=order_question_id[1])
        try:
            batch_question_order = BatchQuestionOrder.objects.get(question=question, batch=batch)
            batch_question_order.order = order_question_id[0]
            batch_question_order.save()
        except BatchQuestionOrder.DoesNotExist:
            BatchQuestionOrder.objects.create(question=question, batch=batch, order=order_question_id[0])

    @classmethod
    def get_batch_order_specific_questions(cls, batch, filter_condition):
        batch_question_orders = BatchQuestionOrder.objects.select_related('question__subquestion','question__group').prefetch_related('question__group__conditions').filter(batch=batch, **filter_condition).order_by('order')
        questions = []
        for batch_question_order in batch_question_orders:
            if not batch_question_order.question.subquestion:
                questions.append(batch_question_order.question)
        return questions


