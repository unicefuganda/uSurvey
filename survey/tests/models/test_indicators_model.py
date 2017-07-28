from django.test import TestCase
from survey.models.indicators import Indicator, IndicatorVariable, IndicatorCriteriaTestArgument
from survey.models.question_module import QuestionModule
from survey.models.surveys import Survey
from survey.models.questions import QuestionSet

class IndicatorTest(TestCase):

    def test_fields(self):
        indicator = Indicator()
        fields = [str(item.attname) for item in indicator._meta.fields]
        self.assertEqual(9, len(fields))
        for field in ['id','created','modified','name','description','survey_id','question_set_id','display_on_dashboard','formulae']:
            self.assertIn(field, fields)

    # def test_store(self):        
    #     survey = Survey.objects.create(name="Survey")        
    #     question_set = QuestionSet.objects.create(name="QuestionSet")
    #     indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", survey=survey, formulae='indicatoir formule', question_set=question_set)
    #     self.failUnless(indicator.id)
    #     self.failUnless(indicator.created)
    #     self.failUnless(indicator.description)
    #     self.failUnless(indicator.name)
    #     self.failUnless(indicator.survey)        
    #     self.failUnless(indicator.formulae)
    #     self.failUnless(indicator.question_set)

    def test_unicode_text(self):
        survey = Survey.objects.create(name="Survey")        
        question_set = QuestionSet.objects.create(name="QuestionSet")
        a = Indicator.objects.create(name="indicator name", description="rajni indicator", survey=survey, formulae='indicatoir formule', question_set=question_set)
        #@a = Indicator.objects.create(name="module name")
        self.assertEqual(a.name, str(a))

    # def setUp(self):
    #     survey = Survey.objects.create(name="Survey")
    #     question_set = QuestionSet.objects.create(name="QuestionSet")
    #     Indicator.objects.create(name='Indicator',description="rajni indicator", survey=survey, formulae='indicatoir formule', question_set=question_set)

    # def test_content(self):
    #     name = Indicator.objects.create(name='Indicator')
    #     description =Indicator.objects.create(description='description')
    #     self.assertEqual(name.name,'Indicator')
    #     self.assertEqual(len(name.name),9)
    #     self.assertEqual(description.description,'description')
    #     self.assertEqual(len(name.name),11)

    # def test_knows_is_a_percentage_indicator(self):
    #     health_module = QuestionModule.objects.create(name="Health")
    #     batch = Batch.objects.create(name="Batch")
    #     indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
    #                                          module=health_module, batch=batch)
    #     self.assertTrue(indicator.is_percentage_indicator())

    # def test_knows_is_not_a_percentage_indicator(self):
    #     health_module = QuestionModule.objects.create(name="Health")
    #     batch = Batch.objects.create(name="Batch")
    #     indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Count',
    #                                          module=health_module, batch=batch)
    #     self.assertFalse(indicator.is_percentage_indicator())

class IndicatorVariableTest(TestCase):
    def test_unicode_text(self):
        iv = IndicatorVariable.objects.create(name="abcd name")
        self.assertEqual(iv.name, str(iv))

class IndicatorCriteriaTestArgumentTest(TestCase):
    def test_unicode_text(self):
        pm = IndicatorCriteriaTestArgument.objects.create(param="abcd name")
        self.assertEqual(pm.param, str(pm))