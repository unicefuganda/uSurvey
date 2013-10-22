from survey.models import Batch, Question, HouseholdMemberGroup, BatchQuestionOrder
from survey.tests.base_test import BaseTest


class BatchQuestionOrderTest(BaseTest):
    def setUp(self):
        self.batch = Batch.objects.create(order=1)
        self.member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        self.question_1 = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER,
                                                  order=1, group=self.member_group)
        self.question_2 = Question.objects.create(text="Question 2?", answer_type=Question.NUMBER,
                                                  order=2, group=self.member_group)
        self.question_1.batches.add(self.batch)
        self.question_2.batches.add(self.batch)

    def test_fields(self):
        batch_question_order = BatchQuestionOrder()
        fields = [str(item.attname) for item in batch_question_order._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created', 'modified', 'batch_id', 'question_id', 'order']:
            self.assertIn(field, fields)

    def test_store(self):
        batch_question_order = BatchQuestionOrder.objects.create(order=1, question=self.question_1, batch=self.batch)
        self.failUnless(batch_question_order.id)
        self.failUnless(batch_question_order.question_id)
        self.failUnless(batch_question_order.batch_id)

    def test_knows_the_order_for_question_is_one_for_first_question_assigned_in_batch(self):
        batch = Batch.objects.create(order=1, name="Batch A")
        self.assertEqual(1, BatchQuestionOrder.next_question_order_for(batch))

    def test_knows_order_is_plus_one_order_of_last_question_assigned_to_batch(self):
        question = Question.objects.create(text="This is a question", answer_type=Question.NUMBER)
        batch = Batch.objects.create(order=1, name="Batch A")
        question.batches.add(batch)

        BatchQuestionOrder.objects.create(question=question, batch=batch, order=1)
        self.assertEqual(2, BatchQuestionOrder.next_question_order_for(batch))

    def test_order_is_not_dependent_on_another_batch(self):
        question = Question.objects.create(text="This is a question", answer_type=Question.NUMBER)
        question_2 = Question.objects.create(text="This is another question", answer_type=Question.NUMBER)
        question_3 = Question.objects.create(text="This is a question in other batch", answer_type=Question.NUMBER)
        batch = Batch.objects.create(order=1, name="Batch A")
        batch_2 = Batch.objects.create(order=2, name="Batch B")
        question.batches.add(batch)
        question_2.batches.add(batch_2)
        question_3.batches.add(batch_2)

        BatchQuestionOrder.objects.create(question=question, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question, batch=batch_2, order=2)
        BatchQuestionOrder.objects.create(question=question, batch=batch_2, order=1)
        self.assertEqual(2, BatchQuestionOrder.next_question_order_for(batch))
        self.assertEqual(3, BatchQuestionOrder.next_question_order_for(batch_2))