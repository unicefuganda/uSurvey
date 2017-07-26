from django.test import TestCase
from survey.models import Indicator, QuestionModule, Survey, QuestionSet


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
    def setUp(self):
        Indicator.objects.create(name='Indicator',description='description')

    def test_content(self):
        name = Indicator.objects.create(name='Indicator')
        description =Indicator.objects.create(description='description')
        self.assertEqual(name.name,'Indicator')
        self.assertEqual(len(name.name),9)
        self.assertEqual(description.description,'description')
        self.assertEqual(len(name.name),11)
    # def test_knows_is_a_percentage_indicator(self):                
    #     survey = Survey.objects.create(name="Survey")
    #     question_set = QuestionSet.objects.create(name="QuestionSet")
    #     indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", survey=survey,
    #                                          formulae="indicator formula", question_set=question_set)
    #     self.assertTrue(indicator.is_open())

    # def test_knows_is_not_a_percentage_indicator(self):        
    #     survey = Survey.objects.create(name="Survey")        
    #     question_set = QuestionSet.objects.create(name="QuestionSet")
    #     indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", survey=survey,
    #                                          formulae="indicator formula", question_set=question_set)
    #     self.assertFalse(indicator.is_open())
