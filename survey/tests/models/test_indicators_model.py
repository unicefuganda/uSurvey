from django.test import TestCase
from survey.models.indicators import Indicator, IndicatorVariable, IndicatorCriteriaTestArgument, IndicatorVariableCriteria
from survey.models.question_module import QuestionModule
from survey.models.surveys import Survey
from survey.models.questions import QuestionSet
from survey.models import Indicator, QuestionModule, Batch

class IndicatorTest(TestCase):

    def test_fields(self):
        indicator = Indicator()
        fields = [str(item.attname) for item in indicator._meta.fields]
        self.assertEqual(9, len(fields))
        for field in ['id','created','modified','name','description','survey_id','question_set_id','display_on_dashboard','formulae']:
            self.assertIn(field, fields)

    def test_store(self):
        survey = Survey.objects.create(name="Survey")
        question_set = QuestionSet.objects.create(name="QuestionSet")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", survey=survey, formulae='indicatoir formule', question_set=question_set)
        self.failUnless(indicator.id)
        self.failUnless(indicator.created)
        self.failUnless(indicator.description)
        self.failUnless(indicator.name)
        self.failUnless(indicator.survey)
        self.failUnless(indicator.formulae)
        self.failUnless(indicator.question_set)

    def test_store(self):
        self.survey = Survey.objects.create(name="say",has_sampling=True,sample_size=1)
        self.questionset = QuestionSet.objects.create(name="santh")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator",display_on_dashboard=True,formulae="formulae",question_set_id=self.questionset.id,survey_id=self.survey.id)
        self.failUnless(indicator.id)
        self.failUnless(indicator.created)
        self.failUnless(indicator.description)
        self.failUnless(indicator.name)
        self.failUnless(indicator.display_on_dashboard)
        self.failUnless(indicator.formulae)
        self.failUnless(indicator.question_set_id)
        self.failUnless(indicator.survey_id)

    def test_unicode_text(self):
        survey = Survey.objects.create(name="Survey")
        question_set = QuestionSet.objects.create(name="QuestionSet")
        a = Indicator.objects.create(name="indicator name", description="rajni indicator", survey=survey, formulae='indicatoir formule', question_set=question_set)        
        self.assertEqual(a.name, str(a))

class IndicatorVariableTest(TestCase):
    
    def test_unicode_text(self):
        iv = IndicatorVariable.objects.create(name="abcd name")
        self.assertEqual(iv.name, str(iv))

class IndicatorCriteriaTestArgumentTest(TestCase):
    
    def test_unicode_text(self):
        dt = IndicatorCriteriaTestArgument.objects.create(criteria_id=1 ,position="1",param="testparam")
        self.assertEqual(dt.param, str(dt))
