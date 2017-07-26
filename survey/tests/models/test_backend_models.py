from django.test import TestCase
from survey.models import Backend

class BackendTest(TestCase):

    def test_fields(self):
        b = Backend()
        fields = [str(item.attname) for item in b._meta.fields]
        self.assertEqual(2, len(fields))
        for field in ['id', 'name']:
            self.assertIn(field, fields)

    def test_store(self):
        ss = Backend.objects.create(name='abc')
        self.failUnless(ss.id)
        self.failUnless(ss.name)
    
    def setUp(self):
        Backend.objects.create(name="Kampala")

    def test_backend(self):
        name = Backend.objects.get(name="Kampala")        
        self.assertEqual(name.name,'Kampala')        
        self.assertEqual(len(name.name),7)

    def test_unicode_text(self):
        ts1 = Backend.objects.create(name="abc name")
        self.assertEqual(ts1.name, str(ts1)) 
