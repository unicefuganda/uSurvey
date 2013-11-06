from django.test import TestCase
from survey.forms.logic import LogicForm
from survey.models import Question, Batch, QuestionOption, AnswerRule, BatchQuestionOrder


class LogicFormTest(TestCase):
    def test_knows_the_fields_in_form(self):
        logic_form = LogicForm()

        fields = ['condition', 'attribute', 'option', 'value', 'validate_with_question', 'action', 'next_question']
        [self.assertIn(field, logic_form.fields) for field in fields]

    def test_does_not_have_value_and_validate_question_if_question_has_options(self):
        fields = ['value', 'validate_with_question']
        batch = Batch.objects.create(order=1)
        question_with_option = Question.objects.create(text="Question 1?",
                                                       answer_type=Question.MULTICHOICE, order=1)
        question_with_option.batches.add(batch)
        logic_form = LogicForm(question=question_with_option, batch=batch)
        [self.assertNotIn(field, logic_form.fields) for field in fields]

    def test_form_has_validation_error_if_value_attribute_is_selected_and_value_field_is_empty(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['EQUALS'],
                    attribute = 'value',
                    value="")

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Field is required.', logic_form.errors['value'])

    def test_form_is_valid_if_between_condition_is_selected_and_rule_with_range_does_not_exist(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    min_value='200', max_value='1000')

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertTrue(logic_form.is_valid())

    def test_form_is_invalid_if_between_condition_is_selected_and_max_value_is_less_than_min_value(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    min_value=6, max_value=3)

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Logic not created max value must be greater than min value.', logic_form.errors['__all__'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_min_value_field_is_empty(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    min_value="")

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Field is required.', logic_form.errors['min_value'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_max_value_field_is_empty(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    max_value="")

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Field is required.', logic_form.errors['max_value'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_min_value_field_is_alpha_numeric(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    min_value="abc123")

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Min value %s invalid, must be an integer.' % data['min_value'],
                      logic_form.errors['__all__'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_min_value_field_is_negative(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    min_value="-1")

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Min value %s invalid, must be greater than zero.' % data['min_value'],
                      logic_form.errors['__all__'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_max_value_field_is_alpha_numeric(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    max_value="abc123")

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Max value %s invalid, must be an integer.' % data['max_value'],
                      logic_form.errors['__all__'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_max_value_field_is_negative(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    max_value="-1")

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Max value %s invalid, must be greater than zero.' % data['max_value'],
                      logic_form.errors['__all__'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_min_value_field_is_within_range_of_existing_rule(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        rule = AnswerRule.objects.create(question=question_without_option, action=AnswerRule.ACTIONS['END_INTERVIEW'],
                                         condition=AnswerRule.CONDITIONS['BETWEEN'],
                                         validate_with_min_value=1, validate_with_max_value=10, batch=batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    min_value=3, max_value=12)

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Rule on this condition BETWEEN with min value %s is within existing range that already exists.' %data['min_value'],
                      logic_form.errors['__all__'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_max_value_field_is_within_range_of_existing_rule(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        rule = AnswerRule.objects.create(question=question_without_option, action=AnswerRule.ACTIONS['END_INTERVIEW'],
                                         condition=AnswerRule.CONDITIONS['BETWEEN'],
                                         validate_with_min_value=3, validate_with_max_value=10, batch=batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    min_value=1, max_value=8)

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Rule on this condition BETWEEN with max value %s is within existing range that already exists.' %data['max_value'],
                      logic_form.errors['__all__'])

    def test_form_has_validation_error_if_between_condition_is_selected_and_min_and_max_value_range_includes_range_of_existing_rule(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)

        rule = AnswerRule.objects.create(question=question_without_option, action=AnswerRule.ACTIONS['END_INTERVIEW'],
                                         condition=AnswerRule.CONDITIONS['BETWEEN'],
                                         validate_with_min_value=3, validate_with_max_value=8, batch=batch)

        data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['BETWEEN'],
                    attribute = 'value',
                    min_value=1, max_value=10)

        logic_form = LogicForm(question=question_without_option, data=data, batch=batch)
        self.assertFalse(logic_form.is_valid())
        self.assertIn('Rule on this condition BETWEEN within range %s - %s already exists.' %(data['min_value'], data['max_value']),
                      logic_form.errors['__all__'])

    def test_does_not_have_option_if_question_does_not_have_options(self):
        field = 'option'
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                       answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)
        logic_form = LogicForm(question=question_without_option, batch=batch)
        self.assertNotIn(field, logic_form.fields)

    def test_choice_of_attribute_is_value_and_validate_with_question_if_question_does_not_have_options(self):
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)
        question_without_option.batches.add(batch)
        attribute_choices = [('value', 'Value'), ('validate_with_question', "Question")]
        logic_form = LogicForm(question=question_without_option, batch=batch)
        self.assertEqual(2, len(logic_form.fields['attribute'].choices))
        [self.assertIn(attribute_choice, logic_form.fields['attribute'].choices) for attribute_choice in attribute_choices]

    def test_choice_of_attribute_is_option_if_question_has_options(self):
        batch = Batch.objects.create(order=1)
        question_with_option = Question.objects.create(text="Question 1?",
                                                       answer_type=Question.MULTICHOICE, order=1)
        question_with_option.batches.add(batch)

        attribute_choice = ('option', 'Option')
        logic_form = LogicForm(question=question_with_option, batch=batch)
        self.assertEqual(1, len(logic_form.fields['attribute'].choices))
        self.assertIn(attribute_choice, logic_form.fields['attribute'].choices)

    def test_option_field_is_prepopulatad_with_question_options_if_selected_question_is_multi_choice(self):
        field = 'option'
        batch = Batch.objects.create(order=1)
        question_with_option = Question.objects.create(text="Question 1?",
                                                       answer_type=Question.MULTICHOICE, order=1)
        question_with_option.batches.add(batch)
        question_option_1 = QuestionOption.objects.create(question=question_with_option, text="Option 1", order=1)
        question_option_2 = QuestionOption.objects.create(question=question_with_option, text="Option 2", order=2)
        question_option_3 = QuestionOption.objects.create(question=question_with_option, text="Option 3", order=3)

        logic_form = LogicForm(question=question_with_option, batch=batch)
        all_options = [question_option_1, question_option_2, question_option_3]
        option_choices = logic_form.fields[field].choices

        self.assertEqual(3, len(option_choices))
        [self.assertIn((question_option.id, question_option.text), option_choices) for question_option in all_options]

    def test_action_field_has_all_actions_on_load_irrespective_of_question(self):
        field = 'action'
        logic_form = LogicForm()
        skip_to = ('SKIP_TO', 'SKIP TO')
        end_interview = ('END_INTERVIEW', 'END INTERVIEW')
        reconfirm = ('REANSWER', 'RECONFIRM')
        ask_subquestion = ('ASK_SUBQUESTION', 'ASK SUBQUESTION')

        all_actions = [skip_to, end_interview, reconfirm, ask_subquestion]
        action_choices = logic_form.fields[field].choices
        self.assertEqual(4, len(action_choices))
        [self.assertIn(action, action_choices) for action in all_actions]

    def test_choices_for_condition_field_knows_equals_option_is_choice_if_multichoice(self):
        choices_returned = LogicForm().choices_for_condition_field(is_multichoice=True)

        self.assertEqual(1,len(choices_returned))
        self.assertIn(('EQUALS_OPTION', 'EQUALS OPTION'), choices_returned)
        self.assertNotIn(('EQUALS', 'EQUALS'), choices_returned)

    def test_choices_for_condition_field_does_not_know_equals_option_is_choice_if_not_multichoice(self):
        choices_returned = LogicForm().choices_for_condition_field(is_multichoice=False)

        self.assertEqual(6,len(choices_returned))
        self.assertNotIn(('EQUALS_OPTION', 'EQUALS OPTION'), choices_returned)

    def test_condition_field_should_have_equals_option_if_multichoice_question(self):
        field = 'condition'
        batch = Batch.objects.create(order=1)
        question_with_option = Question.objects.create(text="Question 1?",
                                                       answer_type=Question.MULTICHOICE, order=1)
        question_with_option.batches.add(batch)
        logic_form = LogicForm(question=question_with_option, batch=batch)

        self.assertEqual(1,len(logic_form.fields[field].choices))
        self.assertIn(('EQUALS_OPTION', 'EQUALS OPTION'), logic_form.fields[field].choices)
        self.assertNotIn(('EQUALS', 'EQUALS'), logic_form.fields[field].choices)

    def test_should_not_have_min_and_max_value_fields_if_multichoice_question(self):
        min_field = 'min_value'
        max_field = 'max_value'
        batch = Batch.objects.create(order=1)
        question_with_option = Question.objects.create(text="Question 1?",
                                                       answer_type=Question.MULTICHOICE, order=1)
        question_with_option.batches.add(batch)
        logic_form = LogicForm(question=question_with_option, batch=batch)

        self.assertNotIn(min_field, logic_form.fields)
        self.assertNotIn(max_field, logic_form.fields)

    def test_condition_field_should_not_have_equals_option_if_not_multichoice_question(self):
        field = 'condition'
        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                       answer_type=Question.NUMBER, order=1)

        question_without_option.batches.add(batch)
        logic_form = LogicForm(question=question_without_option, batch=batch)
        self.assertEqual(6, len(logic_form.fields[field].choices))
        self.assertNotIn(('EQUALS_OPTION', 'EQUALS OPTION'), logic_form.fields[field].choices)

    def test_next_question_knows_all_sub_questions_if_data_sent_with_action_ask_subquestion(self):
        field = 'next_question'

        batch = Batch.objects.create(order=1)
        question_without_option = Question.objects.create(text="Question 1?",
                                                          answer_type=Question.NUMBER, order=1)

        sub_question1 = Question.objects.create(text="sub question1", answer_type=Question.NUMBER,
                                                subquestion=True, parent=question_without_option)

        sub_question1.batches.add(batch)
        question_without_option.batches.add(batch)

        data= {'action': 'ASK_SUBQUESTION'}
        logic_form = LogicForm(question=question_without_option,data=data, batch=batch)

        self.assertIn((sub_question1.id,sub_question1.text), logic_form.fields[field].choices)

    def test_should_not_add_answer_rule_twice_on_same_option_of_multichoice_question(self):
        batch = Batch.objects.create(order=1)
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                                 answer_type=Question.MULTICHOICE, order=1)
        option_1_1 = QuestionOption.objects.create(question=question_1, text="OPTION 1", order=1)
        option_1_2 = QuestionOption.objects.create(question=question_1, text="OPTION 2", order=2)

        sub_question_1 = Question.objects.create(text="Specify others", answer_type=Question.TEXT,
                                                 subquestion=True, parent=question_1)

        question_1.batches.add(batch)
        sub_question_1.batches.add(batch)

        rule = AnswerRule.objects.create(action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                         condition=AnswerRule.CONDITIONS['EQUALS_OPTION'],
                                         validate_with_option=option_1_1, next_question=sub_question_1, batch=batch)

        data = dict(action=rule.action,
                    condition=rule.condition,
                    option=rule.validate_with_option, next_question=rule.next_question)

        logic_form = LogicForm(question = question_1, data = data, batch=batch)

        self.assertFalse(logic_form.is_valid())

    def test_should_not_add_answer_rule_twice_on_same_value_of_numeric_question(self):
        batch = Batch.objects.create(order=1)
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                                 answer_type=Question.NUMBER, order=1)
        value_1 = 0
        value_2 = 20

        sub_question_1 = Question.objects.create(text="Specify others", answer_type=Question.TEXT,
                                                 subquestion=True, parent=question_1)

        rule = AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                         condition=AnswerRule.CONDITIONS['EQUALS'],
                                         validate_with_value=value_1, next_question=sub_question_1, batch=batch)

        question_1.batches.add(batch)
        sub_question_1.batches.add(batch)

        data = dict(action=rule.action,
                    condition=rule.condition,
                    value=rule.validate_with_value, next_question=rule.next_question)

        logic_form = LogicForm(question = question_1, data = data, batch=batch)

        self.assertFalse(logic_form.is_valid())

        another_data = dict(action=AnswerRule.ACTIONS['END_INTERVIEW'],
                    condition=AnswerRule.CONDITIONS['GREATER_THAN_VALUE'],
                    value=rule.validate_with_value)

        logic_form = LogicForm(question = question_1, data = another_data, batch=batch)

        self.assertTrue(logic_form.is_valid())

    def test_should_not_add_answer_rule_twice_on_same_question_value_of_numeric_question(self):
        batch = Batch.objects.create(order=1)
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1)

        question_2 = Question.objects.create(text="How many members are above 18 years?",
                                             answer_type=Question.NUMBER, order=2)

        question_3 = Question.objects.create(text="Some random question",
                                             answer_type=Question.NUMBER, order=3)
        sub_question_1 = Question.objects.create(text="Specify others", answer_type=Question.TEXT,
                                                 subquestion=True, parent=question_1)

        rule = AnswerRule.objects.create(question=question_1, action=AnswerRule.ACTIONS['ASK_SUBQUESTION'],
                                         condition=AnswerRule.CONDITIONS['EQUALS'],
                                         validate_with_question=question_2, next_question=sub_question_1, batch=batch)

        question_1.batches.add(batch)
        question_2.batches.add(batch)
        question_3.batches.add(batch)

        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)

        sub_question_1.batches.add(batch)


        data = dict(action=rule.action,
                    condition=rule.condition,
                    validate_with_question=rule.validate_with_question, next_question=rule.next_question)

        logic_form = LogicForm(question = question_1, data = data, batch=batch)

        self.assertFalse(logic_form.is_valid())

        another_data = dict(action=rule.action,
                            condition=rule.condition,
                            validate_with_question=question_3.pk)

        logic_form = LogicForm(question = question_1, data = another_data, batch=batch)
        self.assertTrue(logic_form.is_valid())