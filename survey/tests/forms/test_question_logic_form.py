from model_mommy import mommy
from datetime import datetime, date, timedelta
from django.test import TestCase
from survey.models import *
from survey.models.backend import Backend
from survey.forms.logic import LogicForm, LoopingForm


class LogicFormTest(TestCase):

    def setUp(self):
        # create some questions
        self.survey = Survey.objects.create(name='test')
        self.batch = Batch.objects.create(name='test', survey=self.survey)
        self.module = QuestionModule.objects.create(name='test')        
        self.qset = QuestionSet.objects.create(name="Females")
        QuestionSetChannel.objects.create(qset=self.qset, channel=ODKAccess.choice_name())
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest",
                                                     constraint_message="message")

    def test_correct_validators_is_applied_as_per_question_answer_type(self):
        answer_types = Answer.supported_answers()  # different types of questions
        for answer_type in answer_types:
            q = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                        identifier=answer_type.choice_name(), text='test',
                                        answer_type=answer_type.choice_name())
            l = LogicForm(q)
            answer_choice_names = [(validator.__name__, validator.__name__.upper())
                                   for validator in answer_type.validators()]
            self.assertEqual(set(l.fields['condition'].choices), set(answer_choice_names))

    def test_logic_form_has_options_for_multi_type_questions(self):
        for answer_type in [MultiSelectAnswer.choice_name(), MultiChoiceAnswer.choice_name()]:            
            q = Question.objects.create(identifier=answer_type, text="text", answer_type=answer_type,
                                                qset_id=self.qset.id, response_validation_id=1)
            l = LogicForm(q)
            self.assertTrue(l.fields.get('option'))

    def test_logic_form_does_not_have_options_for_non_multi_type_questions(self):
        answer_types = Answer.answer_types()
        for answer_type in answer_types:
            if answer_type not in [MultiSelectAnswer.choice_name(), MultiChoiceAnswer.choice_name()]:                
                q = Question.objects.create(identifier=answer_type, text="text", answer_type=answer_type,
                                                qset_id=self.qset.id, response_validation_id=1)
                l = LogicForm(q)
                self.assertFalse(l.fields.get('option'))

    def test_skip_logic_selection_in_form_question_creates_skip_flow(self):
        '''
        :return:
        '''
        q1 = Question.objects.create(qset=self.qset, response_validation=self.rsp,identifier='test1',
                                     text='test1', answer_type=NumericalAnswer.choice_name())
        q2 = Question.objects.create(qset=self.qset, response_validation=self.rsp,
                                     identifier='test2',
                                     text='test2', answer_type=NumericalAnswer.choice_name())
        q3 = Question.objects.create(qset=self.qset, response_validation=self.rsp,
                                     identifier='test3',
                                     text='test3', answer_type=NumericalAnswer.choice_name())
        q4 = Question.objects.create(qset=self.qset, response_validation=self.rsp,
                                     identifier='test4',
                                     text='test4', answer_type=NumericalAnswer.choice_name())
        q5 = Question.objects.create(qset=self.qset, response_validation=self.rsp,
                                     identifier='test5',
                                     text='test5', answer_type=NumericalAnswer.choice_name())
        test_condition = NumericalAnswer.validators()[0].__name__
        test_param = '15'
        form_data = {
            'action': LogicForm.SKIP_TO,
            'condition': test_condition,
            'value': test_param
        }
        self.qset.start_question = q1
        self.qset.save()
        QuestionFlow.objects.create(question=q1, next_question=q2)
        QuestionFlow.objects.create(question=q2, next_question=q3)
        QuestionFlow.objects.create(question=q3, next_question=q4)
        QuestionFlow.objects.create(question=q4, next_question=q5)
        form = LogicForm(q1, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('next_question', form.errors)
        form_data['next_question'] = q4.pk
        form = LogicForm(q1, data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(QuestionFlow.objects.filter(question_id=q1.id, next_question_id=q4.id).exists())
        qf = QuestionFlow.objects.get(question_id=q1.id, next_question_id=q4.id)
        self.assertTrue(qf.text_arguments.filter(param=test_param).exists())

    def test_subquestion_selection_in_form_question_creates_branch_flow(self):
        '''
        :return:
        '''
        q1 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test1',
                                     text='test1', answer_type=TextAnswer.choice_name())
        q2 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test2',
                                     text='test2', answer_type=TextAnswer.choice_name())
        q3 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test3',
                                     text='test3', answer_type=TextAnswer.choice_name())
        q4 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test4',
                                     text='test4', answer_type=TextAnswer.choice_name())
        q5 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test5',
                                     text='test5', answer_type=TextAnswer.choice_name())
        self.qset.start_question = q1
        self.qset.save()
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q5.id)
        test_condition = TextAnswer.validators()[0].__name__
        test_param = 'Hey you!!'
        form_data = {
            'action': LogicForm.ASK_SUBQUESTION,
            'next_question': q4.pk,
            'condition': test_condition,
            'value': test_param
        }
        form = LogicForm(q1, data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(QuestionFlow.objects.filter(question_id=q1.id, next_question_id=q4.id).exists())
        qf = QuestionFlow.objects.get(question_id=q1.id, next_question_id=q4.id)
        self.assertTrue(qf.text_arguments.filter(param=test_param).exists())

    def test_reanswer_selection_in_form_question_creates_flow_to_same_question(self):
        '''

        :return:
        '''
        q1 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test1',
                                     text='test1', answer_type=DateAnswer.choice_name())
        q2 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test2',
                                     text='test2', answer_type=DateAnswer.choice_name())
        q3 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test3',
                                     text='test3', answer_type=DateAnswer.choice_name())
        q4 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test4',
                                     text='test4', answer_type=DateAnswer.choice_name())
        q5 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test5',
                                     text='test5', answer_type=DateAnswer.choice_name())
        self.qset.start_question = q1
        self.qset.save()
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        test_condition = 'between'
        test_param_upper = datetime.now()
        test_param_lower = datetime.now() - timedelta(days=3)
        form_data = {
            'action': LogicForm.REANSWER,
            'condition': test_condition,
            'min_value': test_param_lower,
            'max_value': test_param_upper
        }
        form = LogicForm(q2, data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(QuestionFlow.objects.filter(question_id=q2.id, next_question_id=q2.id).exists())

    def test_end_interview_selection_in_form_question_creates_flow_to_with_no_next_question(self):
        yes = 'yes'
        no = 'no'
        q1 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test1',
                                     text='test1', answer_type=DateAnswer.choice_name())
        q2 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test2',
                                     text='test2', answer_type=MultiChoiceAnswer.choice_name())
        q_o1 = QuestionOption.objects.create(question_id=q2.id, text=yes, order=1)
        QuestionOption.objects.create(question_id=q2.id, text=no, order=2)
        q3 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test3',
                                     text='test3', answer_type=DateAnswer.choice_name())
        q4 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test4',
                                     text='test4', answer_type=DateAnswer.choice_name())
        q5 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test5',
                                     text='test5', answer_type=DateAnswer.choice_name())
        self.qset.start_question = q1
        self.qset.save()
        QuestionFlow.objects.create(question=q1, next_question=q2)
        QuestionFlow.objects.create(question=q2, next_question=q3)
        QuestionFlow.objects.create(question=q3, next_question=q4)
        QuestionFlow.objects.create(question=q4, next_question=q5)
        test_condition = MultiChoiceAnswer.validators()[0].__name__
        form_data = {
            'action': LogicForm.END_INTERVIEW,
            'condition': test_condition,
            'option': q_o1.text
        }
        logic_form = LogicForm(q2, data=form_data)
        self.assertTrue(logic_form.is_valid())
        logic_form.save()
        self.assertTrue(QuestionFlow.objects.filter(question=q2, next_question__isnull=True).exists())

    def test_attempt_to_set_incorrect_value_gives_form_error(self):
        '''
        :return:
        '''
        q1 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test1',
                                     text='test1', answer_type=NumericalAnswer.choice_name())
        q2 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test2',
                                     text='test2', answer_type=NumericalAnswer.choice_name())
        q3 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test3',
                                     text='test3', answer_type=NumericalAnswer.choice_name())
        q4 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test4',
                                     text='test4', answer_type=NumericalAnswer.choice_name())
        q5 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test5',
                                     text='test5', answer_type=NumericalAnswer.choice_name())
        test_condition = NumericalAnswer.validators()[0].__name__
        test_param = '6267fe'
        form_data = {
            'action': LogicForm.SKIP_TO,
            'next_question': q4.pk,
            'condition': test_condition,
            'value': test_param
        }
        self.qset.start_question = q1
        self.qset.save()
        QuestionFlow.objects.create(question=q1, next_question=q2)
        QuestionFlow.objects.create(question=q2, next_question=q3)
        QuestionFlow.objects.create(question=q3, next_question=q4)
        QuestionFlow.objects.create(question=q4, next_question=q5)
        l = LogicForm(q1, data=form_data)
        self.assertFalse(l.is_valid())

    def test_specify_wrong_max_value_gives_form_error(self):
        q1 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test1',
                                     text='test1', answer_type=DateAnswer.choice_name())
        q2 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test2',
                                     text='test2', answer_type=DateAnswer.choice_name())
        q3 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test3',
                                     text='test3', answer_type=DateAnswer.choice_name())
        q4 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test4',
                                     text='test4', answer_type=DateAnswer.choice_name())
        q5 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test5',
                                     text='test5', answer_type=DateAnswer.choice_name())
        self.qset.start_question = q1
        self.qset.save()
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        test_condition = 'between'
        test_param_upper = 'now()'
        test_param_lower = datetime.now() - timedelta(days=3)
        form_data = {
            'action': LogicForm.REANSWER,
            'condition': test_condition,
            'min_value': test_param_lower,
            'max_value': test_param_upper
        }
        l = LogicForm(q2, data=form_data)
        self.assertFalse(l.is_valid())

    def test_specify_wrong_min_value_gives_form_error(self):
        '''
        :return:
        '''
        q1 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test1',
                                     text='test1', answer_type=DateAnswer.choice_name())
        q2 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test2',
                                     text='test2', answer_type=DateAnswer.choice_name())
        q3 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test3',
                                     text='test3', answer_type=DateAnswer.choice_name())
        q4 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test4',
                                     text='test4', answer_type=DateAnswer.choice_name())
        q5 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test5',
                                     text='test5', answer_type=DateAnswer.choice_name())
        self.qset.start_question = q1
        self.qset.save()
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        test_condition = 'between'
        test_param_upper = datetime.now()
        test_param_lower = 'some time ago'
        form_data = {
            'action': LogicForm.REANSWER,
            'condition': test_condition,
            'min_value': test_param_lower,
            'max_value': test_param_upper
        }
        l = LogicForm(q2, data=form_data)
        self.assertFalse(l.is_valid())

    def test_skip_logic_btween_question_groups_not_allowed(self):
        '''
        :return:
        '''
        group = mommy.make(RespondentGroup)
        q1 = BatchQuestion.objects.create(qset=self.batch, response_validation=self.rsp, identifier='test1',
                                          text='test1', answer_type=NumericalAnswer.choice_name())
        q2 = BatchQuestion.objects.create(qset=self.batch, response_validation=self.rsp,
                                          identifier='test2', text='test2', answer_type=NumericalAnswer.choice_name())
        q3 = BatchQuestion.objects.create(qset=self.batch, response_validation=self.rsp, identifier='test3',
                                          text='test3', answer_type=NumericalAnswer.choice_name())
        q4 = BatchQuestion.objects.create(qset=self.batch, response_validation=self.rsp, identifier='test45',
                                          text='test45', answer_type=NumericalAnswer.choice_name(), group=group)
        q5 = BatchQuestion.objects.create(qset=self.batch, response_validation=self.rsp, identifier='test5',
                                          text='test5', answer_type=NumericalAnswer.choice_name())
        test_condition = NumericalAnswer.validators()[0].__name__
        test_param = '15'
        form_data = {
            'action': LogicForm.SKIP_TO,
            'next_question': q4.pk,
            'condition': test_condition,
            'value': test_param
        }
        self.batch.start_question = q1
        self.batch.save()
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        form = LogicForm(q1, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('between questions of different groups is not allowed', form.errors['next_question'][0])


class LoopFlowExtra(TestCase):

    def setUp(self):
        # create some questions
        self.survey = Survey.objects.create(name='test')
        self.batch = Batch.objects.create(name='test', survey=self.survey)
        self.module = QuestionModule.objects.create(name='test')
        self.qset = QuestionSet.objects.create(name="Females")
        QuestionSetChannel.objects.create(qset=self.qset, channel=ODKAccess.choice_name())

    def test_loop_form_fixed_count(self):
        q1 = BatchQuestion.objects.create(qset=self.batch, identifier='test1',
                                          text='test1', answer_type=NumericalAnswer.choice_name())
        q2 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1,
                                          identifier='test2', text='test2', answer_type=NumericalAnswer.choice_name())
        q3 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test3',
                                          text='test3', answer_type=NumericalAnswer.choice_name())
        q4 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test45',
                                          text='test45', answer_type=NumericalAnswer.choice_name())
        q5 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test5',
                                          text='test5', answer_type=NumericalAnswer.choice_name())
        self.batch.start_question = q1
        self.batch.save()
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        form_data = {
            'loop_starter': q1.id,
            'loop_ender': q4.pk,
            'repeat_logic': LoopingForm.FIXED_COUNT,
        }
        form = LoopingForm(q1, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('repeat count is required', form.errors.values()[0])
        form_data['repeat_count'] = 5
        form = LoopingForm(q1, data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(QuestionLoop.objects.count(), 1)
        self.assertTrue(QuestionLoop.objects.filter(loop_starter=q1, loop_ender=q4).exists())

    def test_loop_form_previous_question(self):
        q1 = BatchQuestion.objects.create(qset=self.batch, identifier='test1',
                                          text='test1', answer_type=NumericalAnswer.choice_name())
        q2 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1,
                                          identifier='test2', text='test2', answer_type=TextAnswer.choice_name())
        q3 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test3',
                                          text='test3', answer_type=NumericalAnswer.choice_name())
        q4 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test45',
                                          text='test45', answer_type=NumericalAnswer.choice_name())
        q5 = BatchQuestion.objects.create(qset=self.batch, response_validation_id=1, identifier='test5',
                                          text='test5', answer_type=NumericalAnswer.choice_name())
        self.batch.start_question = q1
        self.batch.save()
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        form_data = {
            'loop_starter': q3.pk,
            'loop_ender': q5.pk,
            'repeat_logic': LoopingForm.PREVIOUS_ANSWER_COUNT,
        }
        form = LoopingForm(q3, data=form_data)
        self.assertFalse(form.is_valid())
        form_data['previous_numeric_values'] = q2.id
        form = LoopingForm(q3, data=form_data)
        self.assertFalse(form.is_valid())               # only numeric answers are allowed as previous questions
        form_data['previous_numeric_values'] = q1.id
        form = LoopingForm(q3, data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(QuestionLoop.objects.filter(loop_starter=q3, loop_ender=q5).count(), 1)
        self.assertTrue(QuestionLoop.objects.filter(loop_starter=q3, loop_ender=q5).exists())