from django.test import TestCase
from survey.models import Indicator, QuestionModule, Batch


class IndicatorTest(TestCase):
    def test_fields(self):
        indicator = Indicator()
        fields = [str(item.attname) for item in indicator._meta.fields]
        self.assertEqual(8, len(fields))
        for field in ['id', 'created', 'modified', 'module_id', 'name', 'description', 'measure', 'batch_id']:
            self.assertIn(field, fields)

    def test_store(self):
        health_module = QuestionModule.objects.create(name="Health")
        batch = Batch.objects.create(name="Batch")
        indicator = Indicator.objects.create(name="indicator name", description="rajni indicator", measure='percentage',
                                             module=health_module, batch=batch)
        self.failUnless(indicator.id)
        self.failUnless(indicator.created)
        self.failUnless(indicator.description)
        self.failUnless(indicator.name)
        self.failUnless(indicator.measure)
        self.failUnless(indicator.batch)
        self.failUnless(indicator.module)