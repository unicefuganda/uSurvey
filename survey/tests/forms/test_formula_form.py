from django.test import TestCase
from survey.forms.formula import FormulaForm
from survey.models import Indicator, QuestionModule, Batch, Survey, Question, HouseholdMemberGroup, Formula


class FormulaFormTest(TestCase):

    def setUp(self):
        self.survey = Survey.objects.create(name='survey name', description='survey descrpition',
                                            sample_size=10)
        self.module = QuestionModule.objects.create(
            name='Education', description='Educational Module')
        self.another_module = QuestionModule.objects.create(
            name='Health', description='Health Module')

        self.group = HouseholdMemberGroup.objects.create(
            name="Females", order=1)
        self.batch = Batch.objects.create(
            order=1, name="Batch A", survey=self.survey)
        self.question_1 = Question.objects.create(identifier='1.1', text="This is a question", answer_type='Numerical Answer',
                                                  group=self.group, batch=self.batch, module=self.module)
        self.question_2 = Question.objects.create(identifier='1.2', text="This is a question", answer_type='Numerical Answer',
                                                  group=self.group, batch=self.batch, module=self.module)
        self.question_3 = Question.objects.create(identifier='1.3', text="This is a question", answer_type='Numerical Answer',
                                                  group=self.group, batch=self.batch, module=self.module)
        self.question_4 = Question.objects.create(identifier='1.4', text="This is a question", answer_type='Numerical Answer',
                                                  group=self.group, batch=self.batch, module=self.module)

        self.percentage_indicator = Indicator.objects.create(name='Test Indicator', measure=Indicator.MEASURE_CHOICES[0][1],
                                                             module=self.module, description="Indicator 1", batch=self.batch)
        self.count_indicator = Indicator.objects.create(name='Test Indicator', measure=Indicator.MEASURE_CHOICES[1][1],
                                                        module=self.module, description="Indicator 1", batch=self.batch)

    def test_should_have_numerator_and_denominator_fields_and_not_count_if_indicator_is_percentage_indicator(self):

        formula_form = FormulaForm(indicator=self.percentage_indicator)

        fields = ['numerator', 'numerator_options', 'denominator_type',
                  'groups', 'denominator', 'denominator_options']
        deleted_fields = ['count']

        [self.assertIn(field, formula_form.fields) for field in fields]
        [self.assertNotIn(field, formula_form.fields)
         for field in deleted_fields]

    def test_should_have_count_fields_if_indicator_is_percentage_indicator(self):

        formula_form = FormulaForm(indicator=self.count_indicator)

        fields = ['count', 'denominator_type', 'groups', 'denominator_options']
        deleted_fields = ['numerator', 'numerator_options', 'denominator']

        [self.assertIn(field, formula_form.fields) for field in fields]
        [self.assertNotIn(field, formula_form.fields)
         for field in deleted_fields]

    def test_should_have_only_questions_for_batch_in_numerator_and_denominator_for_percentage_indicator_in_module(self):
        formula_form = FormulaForm(indicator=self.percentage_indicator)

        [self.question_1, self.question_2]
        [self.question_3, self.question_4]

        self.assertIn((self.group.id, self.group.name),
                      formula_form.fields['groups'].choices)

    def test_should_have_only_questions_for_batch_in_count_for_count_indicator(self):
        formula_form = FormulaForm(indicator=self.count_indicator)

        [self.question_1, self.question_2]
        questions_not_in_batch = [self.question_3, self.question_4]
        [self.assertNotIn((question.id, question.text), formula_form.fields[
                          'count'].choices) for question in questions_not_in_batch]

    def test_should_not_be_valid_if_percentage_indicator_and_formula_with_same_numerator_and_denominator_exists(self):

        form_data = {'numerator': self.question_1.id,
                     'denominator': self.question_2.id,
                     'denominator_type': 'QUESTION'}

        Formula.objects.create(numerator=self.question_1, denominator=self.question_2,
                               indicator=self.percentage_indicator)

        formula_form = FormulaForm(
            indicator=self.percentage_indicator, data=form_data)
        self.assertFalse(formula_form.is_valid())
        self.assertIn('Formula already exist for indicator %s.' %
                      self.percentage_indicator.name, formula_form.errors['__all__'])

    def test_valid_if_percentage_indicator_and_formula_with_same_numerator_and_denominator_does_not_exists(self):
        form_data = {'numerator': self.question_1.id,
                     'denominator': self.question_2.id,
                     'denominator_type': 'QUESTION'}

        formula_form = FormulaForm(
            indicator=self.percentage_indicator, data=form_data)
        self.assertFalse(formula_form.is_valid())

    def test_should_not_be_valid_if_count_indicator_and_formula_with_same_count_questions_exists(self):

        form_data = {'count': self.question_1.id,
                     'denominator_type': 'QUESTION'}

        Formula.objects.create(count=self.question_1,
                               indicator=self.count_indicator)

        formula_form = FormulaForm(
            indicator=self.count_indicator, data=form_data)
        self.assertFalse(formula_form.is_valid())
        self.assertIn('Formula already exist for indicator %s.' %
                      self.percentage_indicator.name, formula_form.errors['__all__'])

    def test_should_not_be_valid_if_count_indicator_and_formula_with_same_groups_exists(self):

        form_data = {'numerator': self.question_1.id,
                     'groups': self.group.id,
                     'denominator_type': 'GROUP'}

        Formula.objects.create(numerator=self.question_1,
                               groups=self.group, indicator=self.count_indicator)

        formula_form = FormulaForm(
            indicator=self.count_indicator, data=form_data)
        self.assertFalse(formula_form.is_valid())
        self.assertIn('Formula already exist for indicator %s.' %
                      self.count_indicator.name, formula_form.errors['__all__'])

    def test_should_not_be_valid_if_percentage_indicator_and_formula_with_same_groups_exists(self):

        form_data = {'numerator': self.question_1.id,
                     'groups': self.group.id,
                     'denominator_type': 'GROUP'}

        Formula.objects.create(
            numerator=self.question_1, groups=self.group, indicator=self.percentage_indicator)

        formula_form = FormulaForm(
            indicator=self.percentage_indicator, data=form_data)
        self.assertFalse(formula_form.is_valid())
        self.assertIn('Formula already exist for indicator %s.' %
                      self.percentage_indicator.name, formula_form.errors['__all__'])

    def test_should_be_valid_if_count_indicator_and_formula_with_same_count_questions_does_not_exist(self):
        form_data = {'count': self.question_1.id,
                     'denominator_type': 'QUESTION'}

        formula_form = FormulaForm(
            indicator=self.count_indicator, data=form_data)
        self.assertFalse(formula_form.is_valid())
