from django.test import TestCase
from survey.forms.question import *
from survey.models import Batch, Survey
from survey.models.questions import Question
from survey.models.householdgroups import HouseholdMemberGroup


class QuestionFormTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(name="Test Survey",description="Desc",sample_size=10,has_sampling=True)
        self.household_member_group = HouseholdMemberGroup.objects.create(name='Age 4-5', order=1)
        self.question_module = QuestionModule.objects.create(name="Education")
        self.batch = Batch.objects.create(name='Batch A',description='description', survey=self.survey)
        self.question = Question.objects.create(identifier='1.1',text="This is a question", answer_type='Numerical Answer',
                                           group=self.household_member_group,batch=self.batch,module=self.question_module)
        self.batch.start_question=self.question
        self.form_data = {
                        'batch': self.batch,
                        'text': 'whaat?',
                        'answer_type': 'Numerical Answer',
                        'identifier': 'ID 1',
                        'options':"some option text",
                        'group' : self.household_member_group.id,
                        'module' : self.question_module.id
        }

    # def test_valid(self):
    #     question_form = QuestionForm(self.batch)
    #     question_form.is_valid()
    #     self.assertTrue(question_form.is_valid())

    def test_invalid(self):
        question_form = QuestionForm(self.batch)
        self.assertFalse(question_form.is_valid())

    def test_question_form_fields(self):
        question_form = QuestionForm(self.batch)
        fields = ['module', 'text', 'answer_type', 'group']
        [self.assertIn(field, question_form.fields) for field in fields]

    def test_question_form_has_tuple_of_all_question_modules_as_choices(self):
        health_module = QuestionModule.objects.create(name="Health")
        education_module = QuestionModule.objects.create(name="Education")
        question_modules = [health_module, education_module]
        question_form = QuestionForm(self.batch)
        [self.assertIn((module.id, module.name), question_form.fields['module'].choices) for module in question_modules]

    def test_question_form_has_no_choices_if_there_are_no_question_modules(self):
        QuestionModule.objects.all().delete()
        question_form = QuestionForm(self.batch)
        self.assertEqual(0, len(question_form.fields['module'].choices))

    # def test_should_know_household_member_group_id_and_name_tuple_is_the_group_choice(self):
    #     question_form = QuestionForm(self.batch)
    #     option1 = QuestionOption.objects.create(question=self.question, text="This is an option1",order=1)
    #     option2 = QuestionOption.objects.create(question=self.question, text="This is an option2",order=2)
    #     self.assertEqual(question_form.fields['group'].choices, [(self.household_member_group.id, self.household_member_group.name)])

    # def test_should_not_save_multichoice_question_if_no_options_given(self):
    #     form_data = self.form_data.copy()
    #     form_data['answer_type'] = "Multi Choice Answer"
    #     form_data['options']=''
    #     question_form = QuestionForm(self.batch)
    #     self.assertFalse(question_form.is_valid())
    #     expected_form_error = 'Question Options missing.'
    #     print question_form.errors.keys(),"++++++++++++++++++++++"
    #     self.assertEqual(1, len(question_form.errors['answer_type']))
    #     self.assertEqual(expected_form_error, question_form.errors['answer_type'][0])
    #
    # def test_should_save_options_and_batch_attached_to_questions_if_supplied(self):
    #     form_data = self.form_data.copy()
    #     form_data['answer_type'] = "Multi Choice Answer"
    #     form_data['options']=['option 1', 'option 2']
    #     question_form = QuestionForm(form_data)
    #     self.assertTrue(question_form.is_valid())
    #     batch = Batch.objects.create()
    #     question = question_form.save(batch=batch, group=[self.household_member_group.id])
    #     self.assertEqual(1, question.batches.all().count())
    #     self.assertEqual(batch, question.batches.all()[0])
    #     options = question.options.all()
    #     self.assertEqual(2, options.count())
    #     self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), options)
    #     self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), options)
    #
    # def test_should_save_questions_and_options_even_if_batch_is_not_supplied(self):
    #     form_data = self.form_data.copy()
    #     form_data['answer_type'] = Question.MULTICHOICE
    #     form_data['options']=['option 1', 'option 2']
    #     question_form = QuestionForm(form_data)
    #     self.assertTrue(question_form.is_valid())
    #     question = question_form.save(group=[self.household_member_group.id])
    #     self.assertEqual(0, len(question.batches.all()))
    #     options = question.options.all()
    #     self.assertEqual(2, options.count())
    #     self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), options)
    #     self.assertIn(QuestionOption.objects.get(text=form_data['options'][0]), options)
    #
    # def test_should_edit_options_text_and_order_of_question_if_supplied(self):
    #     form_data = self.form_data.copy()
    #     form_data['answer_type'] = Question.MULTICHOICE
    #     form_data['options']=['option 1', 'option 2']
    #     question_form = QuestionForm(form_data)
    #
    #     question = question_form.save(group=[self.household_member_group.id])
    #
    #     form_data['options'] = ['option 2', 'option aaaaaaa 1']
    #
    #     question_form = QuestionForm(instance=question, data=form_data)
    #
    #     edited_question = question_form.save(group=[self.household_member_group.id])
    #
    #     options = question.options.all()
    #     self.assertEqual(2, options.count())
    #     self.assertEqual(QuestionOption.objects.get(text=form_data['options'][0], order=1), options[0])
    #     self.assertEqual(QuestionOption.objects.get(text=form_data['options'][1], order=2), options[1])
    #     self.failIf(QuestionOption.objects.filter(text='options 1'))
    #     self.assertEqual(question.id, edited_question.id)
    #
    # def test_should_not_save_options_if_not_multichoice_even_if_options_supplied(self):
    #     form_data = self.form_data.copy()
    #     form_data['answer_type'] = Question.TEXT
    #     form_data['options']=['some option question']
    #     question_form = QuestionForm(form_data)
    #     self.assertTrue(question_form.is_valid())
    #     question = question_form.save(group=[self.household_member_group.id])
    #     self.assertEqual(0, question.batches.all().count())
    #     self.assertEquals(0, question.options.all().count())
    #
    # def test_should_filter_options_not_supplied(self):
    #     form_data = self.form_data.copy()
    #     form_data['answer_type'] = Question.TEXT
    #     del form_data['options']
    #     question_form = QuestionForm(form_data)
    #     self.assertTrue(question_form.is_valid())
    #     question = question_form.save(group=[self.household_member_group.id])
    #     self.assertEqual(0, question.batches.all().count())
    #     self.assertEquals(0, question.options.all().count())
    #
    # def test_form_should_not_be_valid_for_subquestion_if_same_subquestion_already_exist(self):
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1,
    #                                        group=self.household_member_group, identifier='Q1')
    #     sub_question = Question.objects.create(text="this is a sub question", answer_type=Question.NUMBER,
    #                                            subquestion=True, parent=question, group=self.household_member_group,
    #                                            identifier='Q2')
    #
    #     question.batches.add(self.batch)
    #     sub_question.batches.add(self.batch)
    #
    #     form_data = self.form_data.copy()
    #     form_data['text'] = sub_question.text
    #     form_data['answer_type'] = sub_question.answer_type
    #     del form_data['options']
    #     question_form = QuestionForm(data=form_data, parent_question=sub_question.parent)
    #     self.assertFalse(question_form.is_valid())
    #     message= "Sub question for this question with this text already exists."
    #     self.assertIn(message, question_form.errors.values()[0])
    #
    # def test_form_has_parent_groups_only_if_parent_question_is_supplied(self):
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1,
    #                                        group=self.household_member_group, identifier='Q1')
    #
    #     another_member_group = HouseholdMemberGroup.objects.create(name='Age 6-7', order=2)
    #
    #     question_form = QuestionForm(parent_question=question)
    #
    #     self.assertIn((self.household_member_group.id, self.household_member_group.name), question_form.fields['group'].choices)
    #     self.assertNotIn((another_member_group.id, another_member_group.name), question_form.fields['group'].choices)
    #
    # def test_form_has_no_groups_only_if_parent_question_has_no_group_and_is_supplied(self):
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1, identifier='Q1')
    #
    #     another_member_group = HouseholdMemberGroup.objects.create(name='Age 6-7', order=2)
    #
    #     question_form = QuestionForm(parent_question=question)
    #
    #     self.assertNotIn((self.household_member_group.id, self.household_member_group.name), question_form.fields['group'].choices)
    #     self.assertNotIn((another_member_group.id, another_member_group.name), question_form.fields['group'].choices)
    #
    # def test_form_has_all_groups_only_if_no_parent_question_is_supplied(self):
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1,
    #                                        group=self.household_member_group, identifier='Q1')
    #
    #     another_member_group = HouseholdMemberGroup.objects.create(name='Age 6-7', order=2)
    #
    #     question_form = QuestionForm()
    #
    #     self.assertIn((self.household_member_group.id, self.household_member_group.name), question_form.fields['group'].choices)
    #     self.assertIn((another_member_group.id, another_member_group.name), question_form.fields['group'].choices)
    #
    # def test_form_is_invalid_if_parent_question_group_is_different_from_subquestion_group(self):
    #     another_member_group = HouseholdMemberGroup.objects.create(name='Age 6-7', order=2)
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1,
    #                                         group=another_member_group, identifier='Q1')
    #
    #     question_form = QuestionForm(parent_question=question, data=self.form_data)
    #
    #     self.assertFalse(question_form.is_valid())
    #     error_message = "Subquestions cannot have a different group from its parent."
    #     self.assertEqual([error_message], question_form.errors['group'])
    #
    # def test_form_is_invalid_if_module_not_selected(self):
    #     form_data = self.form_data.copy()
    #     form_data['module'] = ''
    #
    #     question_form = QuestionForm(form_data)
    #     self.assertFalse(question_form.is_valid())
    #
    # def test_form_has_parent_module_only_if_parent_question_has_one(self):
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1,
    #                                         module=self.question_module, identifier='Q1')
    #
    #     another_module = QuestionModule.objects.create(name="haha")
    #
    #     question_form = QuestionForm(parent_question=question)
    #
    #     self.assertIn((self.question_module.id, self.question_module.name), question_form.fields['module'].choices)
    #     self.assertNotIn((another_module.id, another_module.name), question_form.fields['module'].choices)
    #
    # def test_form_has_all_module_if_parent_question_has_no_module(self):
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1,
    #                                         identifier='Q1')
    #
    #     another_module = QuestionModule.objects.create(name="haha")
    #
    #     question_form = QuestionForm(parent_question=question)
    #
    #     self.assertEqual(2, len(question_form.fields['module'].choices))
    #     self.assertIn((self.question_module.id, self.question_module.name), question_form.fields['module'].choices)
    #     self.assertIn((another_module.id, another_module.name), question_form.fields['module'].choices)
    #
    # def test_form_has_all_module_if_parent_question_is_not_supplied(self):
    #     another_module = QuestionModule.objects.create(name="haha")
    #
    #     question_form = QuestionForm()
    #
    #     self.assertEqual(2, len(question_form.fields['module'].choices))
    #     self.assertIn((self.question_module.id, self.question_module.name), question_form.fields['module'].choices)
    #     self.assertIn((another_module.id, another_module.name), question_form.fields['module'].choices)
    #
    # def test_form_is_invalid_if_parent_question_module_is_different_from_subquestion_module(self):
    #     another_module = QuestionModule.objects.create(name="haha")
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1,
    #                                         module=another_module, identifier='Q1')
    #
    #     question_form = QuestionForm(parent_question=question, data=self.form_data)
    #
    #     self.assertFalse(question_form.is_valid())
    #     error_message = "Subquestions cannot have a different module from its parent."
    #     self.assertEqual([error_message], question_form.errors['module'])
    #
    # def test_form_is_invalid_if_trying_to_add_duplicate_subquestion_under_question(self):
    #     question = Question.objects.create(text="Question 1?", answer_type=Question.NUMBER, order=1,
    #                                        group=self.household_member_group, identifier='Q1')
    #
    #     sub_question_data = {'text': 'Subquestion 1?',
    #                          'answer_type':Question.NUMBER,
    #                          'group': self.household_member_group,
    #                          'identifier': 'ID 1',
    #                          'subquestion': True,
    #                          'parent': question}
    #
    #     sub_question = Question.objects.create(**sub_question_data)
    #     error_message = 'Sub question for this question with this text already exists.'
    #
    #     sub_question_data['group'] = self.household_member_group.id
    #     question_form = QuestionForm(parent_question=question, data=sub_question_data)
    #     is_valid = question_form.is_valid()
    #     self.assertFalse(is_valid)
    #     self.assertIn(error_message, question_form.errors['text'])
    #
    #
