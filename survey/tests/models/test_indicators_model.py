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
        # health_module = QuestionModule.objects.create(name="Health")
        # batch = Batch.objects.create(name="Batch")
        # indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
        #                                      module=health_module, batch=batch)
        self.survey = Survey.objects.create(name="say",has_sampling=True,sample_size=1)
        self.questionset = QuestionSet.objects.create(name="santh")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator",display_on_dashboard=True,formulae="formulae",question_set_id=self.questionset.id,survey_id=self.survey.id)
        self.failUnless(indicator.id)
        self.failUnless(indicator.created)
        self.failUnless(indicator.description)
        self.failUnless(indicator.name)
        # self.failUnless(indicator.measure)
        # self.failUnless(indicator.batch)
        # self.failUnless(indicator.module)
        self.failUnless(indicator.display_on_dashboard)
        self.failUnless(indicator.formulae)
        self.failUnless(indicator.question_set_id)
        self.failUnless(indicator.survey_id)

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

    # def setUp(self):
    #     # self.survey = Survey.objects.create(name="Survey")
    #     # self.question_set = QuestionSet.objects.create(question_set='question_set')
    #     self.survey = Survey.objects.create(name="Survey")        
    #     self.question_set = QuestionSet.objects.create(name="QuestionSet")
    #     self.indic = Indicator.objects.create(name="dummy",description="abcd",survey=self.survey,question_set=self.question_set,formulae='indicatoir formule')
    #     self.indvar = IndicatorVariable.objects.create(name="ind",description="desc",indicator=self.indic)        
    #     self.question = Question.objects.create(qset=self.question_set)
    #     self.indvarcri = IndicatorVariableCriteria.objects.create(variable=self.indvar,test_question=self.question,validation_test="validationtest")
    #     self.icta = IndicatorCriteriaTestArgument.objects.create(criteria=self.indvarcri,position="1",param="testparam")
    
    def test_unicode_text(self):
        dt = IndicatorCriteriaTestArgument.objects.create(criteria_id=1 ,position="1",param="testparam")
        self.assertEqual(dt.param, str(dt))
