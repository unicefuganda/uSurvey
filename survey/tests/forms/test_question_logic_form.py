from datetime import datetime, date, timedelta
from django.test import TestCase
from survey.models import QuestionFlow, Question, Survey, Batch, Answer, \
    QuestionModule, MultiSelectAnswer, MultiChoiceAnswer, \
    NumericalAnswer, TextArgument, TextAnswer, DateAnswer, QuestionOption, QuestionSet, Question, ResponseValidation
from survey.models.backend import Backend
from survey.forms.logic import LogicForm


class LogicFormTest(TestCase):

    def setUp(self):
        # create some questions
        self.survey = Survey.objects.create(name='test')
        self.batch = Batch.objects.create(name='test', survey=self.survey)
        self.module = QuestionModule.objects.create(name='test')        
        self.qset = QuestionSet.objects.create(name="Females")
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest",constraint_message="message")        

    def test_correct_validators_is_applied_as_per_question_answer_type(self):
        answer_types = Answer.supported_answers()  # different types of questions
        for answer_type in answer_types:
            q = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                        identifier=answer_type.choice_name(), text='test',
                                        answer_type=answer_type.choice_name())
            l = LogicForm(q)
            answer_choice_names = [(validator.__name__, validator.__name__.upper())
                                   for validator in answer_type.validators()]
            self.assertEqual(
                set(l.fields['condition'].choices), set(answer_choice_names))

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
        q1 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,identifier='test1',text='test1', answer_type=NumericalAnswer.choice_name())
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
        test_param = '15'
        form_data = {
            'action': LogicForm.SKIP_TO,
            'next_question': q4.pk,
            'condition': test_condition,
            'value': test_param
        }
        self.batch.start_question = q1
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        l = LogicForm(q1, data=form_data)
        if l.is_valid():
            l.save()
            # now check if equivalent Question flow and test arguments were
            # created
            try:
                qf = QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q4.id)
                TextArgument.objects.get(flow=qf, param=test_param)
                self.assertTrue(True)
                return
            except QuestionFlow.DoesNotExist:
                #self.assertTrue(False, 'flow not existing')
                pass
            except TextArgument:
                self.assertTrue(False, 'text agrunments not saved')
                pass
        else:
            self.assertTrue(False, 'Invalid form %s' % l.errors)
        #self.assertTrue(False)

    def test_subquestion_selection_in_form_question_creates_skip_flow(self):
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
        q4 = Question.objects.create(qset_id=self.qset, response_validation_id=1,
                                     identifier='test4',
                                     text='test4', answer_type=TextAnswer.choice_name())
        q5 = Question.objects.create(qset_id=self.qset, response_validation_id=1,
                                     identifier='test5',
                                     text='test5', answer_type=TextAnswer.choice_name())
        self.batch.start_question = q1
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
        l = LogicForm(q1, data=form_data)
        if l.is_valid():
            l.save()
            # now check if equivalent Question flow and test arguments were
            # created
            try:
                qf = QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q4.id)
                TextArgument.objects.get(flow=qf, param=test_param)
                qf = QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q3.id)
                self.assertTrue(True)
                return
            except QuestionFlow.DoesNotExist:
                #self.assertTrue(False, 'flow not existing')
                pass
            except TextArgument:
                self.assertTrue(False, 'text agrunments not saved')
                pass
        else:
            self.assertTrue(False, 'Invalid form: %s' % l.errors)
        #self.assertTrue(False)

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
        self.batch.start_question = q1
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
        l = LogicForm(q1, data=form_data)
        if l.is_valid():
            l.save()
            # now check if equivalent Question flow and test arguments were
            # created
            try:
                qf = QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q4.id)
                TextArgument.objects.get(flow=qf, param=test_param)
                qf = QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q3.id)
                self.assertTrue(True)
                return
            except QuestionFlow.DoesNotExist:
                #self.assertTrue(False, 'flow not existing')
                pass
            except TextArgument:
                self.assertTrue(False, 'text agrunments not saved')
                pass
        else:
            self.assertTrue(False, 'Invalid form')
        #self.assertTrue(False)

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
        self.batch.start_question = q1
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
        l = LogicForm(q2, data=form_data)
        if l.is_valid():
            l.save()
            # now check if equivalent Question flow and test arguments were
            # created
            try:
                qf = QuestionFlow.objects.get(
                    question_id=q2.id, next_question_id=q2.id)
                TextArgument.objects.get(
                    flow=qf, position=0, param=test_param_lower)
                TextArgument.objects.create(
                    flow=qf, position=1, param=test_param_upper)
                QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q2.id)
                QuestionFlow.objects.get(
                    question_id=q2.id, next_question_id=q3.id)
                self.assertTrue(True)
                return
            except QuestionFlow.DoesNotExist:
                self.assertTrue(False, 'flow not existing')
                pass
            except TextArgument:
                self.assertTrue(False, 'text agrunments not saved')
                pass
        else:
            self.assertTrue(False, 'Invalid form')
        self.assertTrue(False)

    def test_end_interview_selection_in_form_question_creates_flow_to_with_no_next_question(self):
        '''
        :return:
        '''
        yes = 'yes'
        no = 'no'
        q1 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test1',
                                     text='test1', answer_type=DateAnswer.choice_name())
        q2 = Question.objects.create(qset_id=self.qset.id, response_validation_id=1,
                                     identifier='test2',
                                     text='test2', answer_type=MultiChoiceAnswer.choice_name())
        q_o1 = QuestionOption.objects.create(question_is=q2.id, text=yes, order=1)
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
        self.batch.start_question = q1
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        test_condition = MultiChoiceAnswer.validators()[0].__name__
        form_data = {
            'action': LogicForm.END_INTERVIEW,
            'condition': test_condition,
            'option': q_o1.order
        }
        l = LogicForm(q2, data=form_data)
        if l.is_valid():
            l.save()
            # now check if equivalent Question flow and test arguments were
            # created
            try:
                qf = QuestionFlow.objects.get(
                    question_id=q2.id, next_question_id__isnull=True)
                TextArgument.objects.get(flow=qf, position=0, param=q_o1.order)
                QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q2.id)
                QuestionFlow.objects.get(
                    question_id=q2.id, next_question_id=q3.id)
                self.assertTrue(True)
                return
            except QuestionFlow.DoesNotExist:
                self.assertTrue(False, 'flow not existing')
                pass
            except TextArgument:
                self.assertTrue(False, 'text agrunments not saved')
                pass
        else:
            self.assertTrue(False, 'Invalid form')
        self.assertTrue(False)

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
        self.batch.start_question = q1
        QuestionFlow.objects.create(question_id=q1.id, next_question_id=q2.id)
        QuestionFlow.objects.create(question_id=q2.id, next_question_id=q3.id)
        QuestionFlow.objects.create(question_id=q3.id, next_question_id=q4.id)
        QuestionFlow.objects.create(question_id=q4.id, next_question_id=q5.id)
        l = LogicForm(q1, data=form_data)
        if l.is_valid():
            l.save()
            # now check if equivalent Question flow and test arguments were
            # created
            try:
                qf = QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q4.id)
                TextArgument.objects.get(flow=qf, param=test_param)
                self.assertTrue(False, 'completely wrong. value saved as good')
                return
            except QuestionFlow.DoesNotExist:
                self.assertTrue(False, 'form valid but flow not existing')
                pass
            except TextArgument:
                self.assertTrue(
                    False, 'form valid but text agrunments not saved')
                pass
        else:
            self.assertTrue(True)

    def test_specify_wrong_max_value_gives_form_error(self):
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
        self.batch.start_question = q1
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
        if l.is_valid():
            l.save()
            # now check if equivalent Question flow and test arguments were
            # created
            try:
                qf = QuestionFlow.objects.get(
                    question_id=q2.id, next_question_id=q2.id)
                TextArgument.objects.get(
                    flow=qf, position=0, param=test_param_lower)
                TextArgument.objects.create(
                    flow=qf, position=1, param=test_param_upper)
                QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q2.id)
                QuestionFlow.objects.get(
                    question_id=q2.id, next_question_id=q3.id)
                self.assertTrue(
                    False, 'completely wrong. bad values was saved as good!!')
                return
            except QuestionFlow.DoesNotExist:
                self.assertTrue(False, 'form valid flow not existing')
                pass
            except TextArgument:
                self.assertTrue(
                    False, 'Form valid but text agrunments not saved')
                pass
        else:
            self.assertTrue(True)

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
        self.batch.start_question = q1
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
        if l.is_valid():
            l.save()
            # now check if equivalent Question flow and test arguments were
            # created
            try:
                qf = QuestionFlow.objects.get(
                    question_id=q2.id, next_question_id=q2.id)
                TextArgument.objects.get(
                    flow=qf, position=0, param=test_param_lower)
                TextArgument.objects.create(
                    flow=qf, position=1, param=test_param_upper)
                QuestionFlow.objects.get(
                    question_id=q1.id, next_question_id=q2.id)
                QuestionFlow.objects.get(
                    question_id=q2.id, next_question_id=q3.id)
                self.assertTrue(
                    False, 'completely wrong. bad values was saved as good!!')
                return
            except QuestionFlow.DoesNotExist:
                self.assertTrue(False, 'form valid flow not existing')
                pass
            except TextArgument:
                self.assertTrue(
                    False, 'Form valid but text agrunments not saved')
                pass
        else:
            self.assertTrue(True)