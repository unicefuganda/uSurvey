from django.test import TestCase
from survey.models import Backend

class BackendTest(TestCase):
    def setUp(self):
        Backend.objects.create(name="Kampala")
    def test_backend(self):
        name = Backend.objects.get(name="Kampala")        
        self.assertEqual(name,'Kampala')        
        self.assertEqual(len(name.name),7)    
