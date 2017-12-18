from model_mommy import mommy
from django.template.defaultfilters import slugify
from django.test import TestCase
from django.test.client import RequestFactory
from django import forms
from survey.forms.answer import *
from survey.forms.form_helper import get_form_field_no_validation
from survey.models import *
from survey.tests.base_test import BaseTest
from survey.tests.models.survey_base_test import SurveyBaseTest


class AnswerFormExtra(SurveyBaseTest):


    def test_answers_ussd_prepend_no_text(self):
        self._create_ussd_non_group_questions(self.qset)
        interview = self.interview

        class TestForm(forms.Form, USSDSerializable):
            value1 = forms.CharField()
        data = {}
        form = TestForm(data=data)
        self.assertEquals(form.render_prepend_ussd(), '')
        self.assertEquals(form.render_extra_ussd(), None)
        self.assertEquals(form.render_extra_ussd_html(), None)

        class TestForm(forms.Form, USSDSerializable):
            value = forms.CharField()
        data = {}
        form = TestForm(data=data)
        self.assertEquals(form.text_error(), form.errors['value'][0])

    def test_form_field_types(self):
        self._create_test_non_group_questions(self.qset)
        geo_question = Question.objects.filter(answer_type=GeopointAnswer.choice_name()).last()
        interview = self.interview
        first_answer_class = Answer.get_class(interview.question_set.start_question.answer_type)
        self.assertEquals(first_answer_class, get_answer_form(interview).Meta.model)
        interview.last_question = geo_question
        interview.save()
        interview = self.interview
        AnswerForm = get_answer_form(interview)
        form = AnswerForm()
        self.assertEquals(form.fields['value'].__class__.__name__,
                          get_form_field_no_validation(forms.CharField).__name__)
        multiselect_question = Question.objects.filter(answer_type=MultiSelectAnswer.choice_name()).last()
        interview = self.interview
        interview.last_question = multiselect_question
        interview.save()
        AnswerForm = get_answer_form(interview)
        form = AnswerForm()
        self.assertTrue(isinstance(form.fields['value'], forms.ModelMultipleChoiceField))
        self.assertEquals(form.fields['value'].queryset.count(), multiselect_question.options.count())
        for opt in multiselect_question.options.all():
            self.assertIn('%s: %s' % (opt.order, opt.text), form.render_extra_ussd_html())
        interview.last_question = Question.objects.filter(answer_type=ImageAnswer.choice_name()).last()
        interview.save()
        AnswerForm = get_answer_form(interview)
        form = AnswerForm()
        self.assertIn('accept', form.fields['value'].widget.attrs)

    def test_form_with_ussd_access(self):
        self._create_test_non_group_questions(self.qset)
        ussd_access = mommy.make(USSDAccess, interviewer=self.interviewer)
        interview = self.interview
        interview.last_question = Question.objects.filter(answer_type=GeopointAnswer.choice_name()).last()
        interview.save()
        AnswerForm = get_answer_form(interview, access=ussd_access)
        data = {'value': '12 89.3 3 5'}
        form = AnswerForm(data=data)
        self.assertTrue(form.is_valid())
        choice_question = Question.objects.filter(answer_type=MultiChoiceAnswer.choice_name()).last()
        interview = self.interview
        interview.last_question = choice_question
        interview.save()
        data = {'value': 'something else'}
        AnswerForm = get_answer_form(interview)
        form = AnswerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('value', form.errors)
        validation = mommy.make(ResponseValidation, validation_test='greater_than')
        mommy.make(TextArgument, validation=validation, position=1, param=20)
        num_question = Question.objects.filter(answer_type=NumericalAnswer.choice_name()).last()
        num_question.response_validation = validation
        num_question.save()
        interview = self.interview
        interview.last_question = num_question
        interview.save()
        data = {'value': 4}
        AnswerForm = get_answer_form(interview)
        form = AnswerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEquals(form.errors['value'][0], validation.dconstraint_message)
        data = {'value': 25}
        form = AnswerForm(data=data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(NumericalAnswer.objects.count(), 1)

    def test_answer_form_with_wrong_option(self):
        self._create_test_non_group_questions(self.qset)
        interview = self.interview
        geo_question = Question.objects.filter(answer_type=GeopointAnswer.choice_name()).last()
        interview.last_question = geo_question
        interview.save()
        data = {'value': 'something else 2 4'}
        AnswerForm = get_answer_form(interview)
        form = AnswerForm(data=data)
        self.assertIn('lat[space]long[space]altitude[space]precision', form.errors['value'][0])

    # def test_loop_answer_for_ussd(self):
    #     ussd_id = '7182829393'
    #     ussd_access = mommy.make(USSDAccess, interviewer=self.interviewer, user_identifier=ussd_id)
    #     self._create_test_non_group_questions(self.qset)
    #     first = Question.objects.first()
    #     last = Question.objects.last()
    #     mommy.make(QuestionLoop, loop_starter=first, loop_ender=last)
    #     request = RequestFactory().get('/')
    #     # first check if the loop form value uses numeric input
    #     data = {'uid': ussd_id}
    #     form = AddMoreLoopForm(data=)
    #
    # def test_add_loop_form_uses_numeric_widget(self):
    #     """ 124, 205, 223-224, 234-236, 247-248, 254-255, 258, 289-291, 321-329, 332-333,
    #     336-339, 342-345, 351-356, 359-360, 363-366, 369-372
    #         """
    #     AddMoreLoopForm9d

