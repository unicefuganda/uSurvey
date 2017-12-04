from model_mommy import mommy
from django.test import TestCase
from survey.models import QuestionModule
from django.db import IntegrityError
from survey.models import *
from survey.tests.models.survey_base_test import SurveyBaseTest


class QuestionTest(TestCase):

    def setUp(self):
        self.question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        self.batch = Batch.objects.create(order=1)

    def test_fields(self):
        ss_content = Question()
        fields = [str(item.attname) for item in ss_content._meta.fields]
        self.assertEqual(9, len(fields))
        for field in ['id', 'created', 'modified', 'identifier', 'text', 'answer_type', 'mandatory',
                      'qset_id', 'response_validation_id']:
            self.assertIn(field, fields)


class QuestionOptionTest(TestCase):

    def test_unicode_text(self):
        opt = QuestionOption.objects.create(text="module name", order=1)
        self.assertEqual(opt.text, str(opt))

    def test_fields(self):
        s_content = QuestionOption()
        fields = [str(item.attname) for item in s_content._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created', 'modified', 'question_id', 'text', 'order']:
            self.assertIn(field, fields)


class QuestionSetTest(TestCase):

    def test_unicode_text(self):
        qst = QuestionSet.objects.create(name="module name")
        self.assertEqual(qst.name, str(qst))


class QuestionTestsExtra(SurveyBaseTest):

    def test_loop_story_with_no_loops_return_empty(self):
        self._create_test_non_group_questions(self.qset)
        question = self.qset.flow_questions[0]
        self.assertEqual(question.loops(), [])
        self.assertEqual(len(self.qset.flow_questions), 10)
        # not create two loops, one nested
        mommy.make(QuestionLoop, loop_starter=self.qset.flow_questions[0], loop_ender=self.qset.flow_questions[-1])
        mommy.make(QuestionLoop, loop_starter=self.qset.flow_questions[1], loop_ender=self.qset.flow_questions[-2])
        self.assertEqual(len(self.qset.flow_questions[3].loops()), 2)

    def test_misallaneous(self):
        self._create_test_non_group_questions(self.qset)
        self.assertEqual(Batch.objects.get(pk=self.qset.id), self.qset.flow_questions[0].e_qset)
        question = Question.objects.filter(answer_type=MultiChoiceAnswer.choice_name()).first()
        old_flow_questions = self.qset.flow_questions
        self.assertNotEquals(question.display_text(), question.text)
        self.assertIn(question.text, question.display_text())
        # question = mommy.make(Question, qset=self.qset, answer_type=NumericalAnswer.choice_name())
        validation = mommy.make(ResponseValidation, validation_test='greater_than')
        mommy.make(TextArgument, validation=validation, position=1, param=20)
        mommy.make(QuestionFlow, desc='SKIP_TO', question=self.qset.flow_questions[2],
                   next_question=self.qset.flow_questions[4], validation=validation)
        self.assertEquals(self.qset.flow_questions[2].flows.count(), 2)
        self.assertEquals(self.qset.flow_questions[2].next_question('4').id,
                          self.qset.flow_questions[4].id)
        self.assertEquals(self.qset.flow_questions[2].upcoming_inlines(), old_flow_questions[2:])
        self.assertEquals(self.qset.flow_questions[2].upcoming_question().id, old_flow_questions[3].id)
        self.assertEquals(self.qset.flow_questions[4].preceeding_conditional_flows().last(),
                          old_flow_questions[2].conditional_flows().last())
        self.assertEquals(self.qset.flow_questions[2].conditional_flows().last().validation_test, 'greater_than')
        self.assertEquals(self.qset.flow_questions[2].conditional_flows().last().text_arguments[0].param, '20')
        self.assertFalse(self.qset.flow_questions[2].flows.filter(validation__isnull=True
                                                                  ).first().text_arguments.exists())
        self.assertEquals(self.qset.flow_questions[2].conditional_flows().last().test_arguments[0].param, '20')
        self.assertEquals(self.qset.flow_questions[1].index_breadcrumbs(), [])
        self.assertEquals(self.qset.flow_questions[1].new_breadcrumbs(qset=self.qset),
                          self.qset.flow_questions[1].edit_breadcrumbs(qset=self.qset))
        # test assigning validation test
        conditional_flow = self.qset.flow_questions[2].conditional_flows().last()
        conditional_flow.validation_test = 'equals'
        self.assertEquals(conditional_flow.validation.validation_test, conditional_flow.validation_test)

    def test_clone_only_start_question(self):
        qset = self.qset1
        #self._create_ussd_non_group_questions(qset)
        question = mommy.make(BatchQuestion, qset=qset)
        qset.start_question = question
        qset.save()
        qset.deep_clone()
        self.assertEquals(Question.objects.filter(qset__name__icontains=qset.name).count(), 2)
        self.assertEquals(Question.objects.filter(qset__name=qset.name).count(), 1)

