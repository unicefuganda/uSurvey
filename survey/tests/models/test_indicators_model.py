from django.test import TestCase
from survey.models import Indicator, QuestionModule, Batch


class IndicatorTest(TestCase):

    def test_fields(self):
        indicator = Indicator()
        fields = [str(item.attname) for item in indicator._meta.fields]
        self.assertEqual(9, len(fields))
        for field in ['id','created','modified','name','description','survey_id','question_set_id','display_on_dashboard','formulae']:
            self.assertIn(field, fields)

    def test_store(self):
        health_module = QuestionModule.objects.create(name="Health")
        batch = Batch.objects.create(name="Batch")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                             module=health_module, batch=batch)
        self.failUnless(indicator.id)
        self.failUnless(indicator.created)
        self.failUnless(indicator.description)
        self.failUnless(indicator.name)
        self.failUnless(indicator.measure)
        self.failUnless(indicator.batch)
        self.failUnless(indicator.module)

    def test_knows_is_a_percentage_indicator(self):
        health_module = QuestionModule.objects.create(name="Health")
        batch = Batch.objects.create(name="Batch")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Percentage',
                                             module=health_module, batch=batch)
        self.assertTrue(indicator.is_percentage_indicator())

    def test_knows_is_not_a_percentage_indicator(self):
        health_module = QuestionModule.objects.create(name="Health")
        batch = Batch.objects.create(name="Batch")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='Count',
                                             module=health_module, batch=batch)
        self.assertFalse(indicator.is_percentage_indicator())
