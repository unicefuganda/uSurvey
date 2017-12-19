from model_mommy import mommy
from django.test import TestCase
from survey.forms.question import *
from survey.models import *
from survey.tests.models.survey_base_test import SurveyBaseTest


class QuestionFormTest(SurveyBaseTest):

    def setUp(self):
        super(QuestionFormTest, self).setUp()
        self.survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        self.question_module = QuestionModule.objects.create(name="Education")
        self.survey = Survey.objects.create(name="Health survey")
        self.batch = Batch.objects.create(name="Health", survey=self.survey)

    def test_question_form_fields(self):
        question_form = QuestionForm(self.batch)
        fields = ['text', 'answer_type']
        [self.assertIn(field, question_form.fields) for field in fields]

    def test_invalid(self):
        question_form = QuestionForm(self.batch)
        self.assertFalse(question_form.is_valid())

    def test_question_form_has_no_choices_if_there_are_no_question_modules(self):
        QuestionModule.objects.all().delete()
        question_form = QuestionForm(self.batch)
        self.assertEqual(1, len(question_form.fields['answer_type'].choices))

    def test_attempt_to_use_invalid_placeholder_fails(self):
        self._create_ussd_non_group_questions()
        all_questions = self.qset.all_questions
        data = {'text': 'This {{non_existent}} thing',  'answer_type': NumericalAnswer.choice_name(),
                'identifier': 'testone'}
        question_form = QuestionForm(self.qset, prev_question=all_questions[-1], data=data)
        self.assertFalse(question_form.is_valid())
        self.assertIn('text', question_form.errors)

    def test_attempt_to_save_group_with_with_param_existing_in_listing_fails(self):
        listing_form = mommy.make(ListingTemplate)
        listing_form.start_question = mommy.make(Question, identifier='testq', qset=listing_form)
        listing_form.save()
        survey = self.qset.survey
        survey.listing_form = listing_form
        survey.has_sampling = True
        survey.save()
        self.qset.refresh_from_db()
        self._create_ussd_non_group_questions()
        all_questions = self.qset.all_questions
        group = mommy.make(RespondentGroup)
        param_question = mommy.make(ParameterTemplate, answer_type=NumericalAnswer.choice_name(),
                                    identifier='testq')
        condition = mommy.make(RespondentGroupCondition, validation_test='greater_than',
                               test_question=param_question, respondent_group=group)
        mommy.make(GroupTestArgument, group_condition=condition, param=7, position=1)
        data = {'text': 'This good stuff',  'answer_type': NumericalAnswer.choice_name(),
                'identifier': 'testq', 'group': group.id, 'qset': self.qset.id}
        question_form = BatchQuestionForm(self.qset, data=data)
        self.assertFalse(question_form.is_valid())
        self.assertIn('group', question_form.errors)




