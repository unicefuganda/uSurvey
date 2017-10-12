from django.test import TestCase
from survey.models import Interviewer, InterviewerAccess, USSDAccess, ODKAccess
from survey.models.base import BaseModel

class InterviewerAccessTest(TestCase):
    
    def test_fields(self):
        access = InterviewerAccess()
        fields = [str(item.attname) for item in access._meta.fields]
        self.assertEqual(8, len(fields))
        for field in ['id','created','modified','user_identifier','is_active','reponse_timeout','duration','interviewer_id']:
            self.assertIn(field, fields)    
    
    def test_store(self):
        interviewer = Interviewer.objects.create(name="Interviewer")
        access = InterviewerAccess.objects.create(user_identifier="identifier name", reponse_timeout="1", interviewer=interviewer,
                                             duration='5')
        self.failUnless(access.id)
        self.failUnless(access.created)
        self.failUnless(access.user_identifier)
        self.failUnless(access.reponse_timeout)
        self.failUnless(access.interviewer)
        self.failUnless(access.duration)
    
    def setUp(self):        
        interviewer = Interviewer.objects.create(name="Interviewer")
        InterviewerAccess.objects.create(user_identifier="useridentifier",reponse_timeout=1,duration="123",interviewer_id=1)
    
    def test_backend(self):        
        user_identifier = InterviewerAccess.objects.get(user_identifier="useridentifier")
        duration = InterviewerAccess.objects.get(duration="123")
        self.assertEqual(user_identifier.user_identifier,'useridentifier')
        self.assertEqual(len(user_identifier.user_identifier),14)
        self.assertEqual(duration.duration,'123')
        self.assertEqual(len(duration.duration),3)
    
    def test_unicode_text(self):
        interviewer = Interviewer.objects.create(name="Interviewer")
        user_identifier = InterviewerAccess.objects.create(user_identifier="abc name", interviewer_id=1)
        self.assertEqual(user_identifier.user_identifier, str(user_identifier))

class USSDAccessTest(TestCase):
    
    def setUp(self):
        interviewer = Interviewer.objects.create(name="Interviewer") 
        intervieweraccess=InterviewerAccess.objects.create(user_identifier="useridentifier",reponse_timeout=1,duration="123",interviewer_id=interviewer.id)
        USSDAccess.objects.create(aggregator="Dummy",interviewer_id=1)

    def test_fields(self):
        ussd = USSDAccess()
        fields = [str(item.attname) for item in ussd._meta.fields]
        self.assertEqual(10, len(fields))
        for field in ['intervieweraccess_ptr_id', 'aggregator']:
            self.assertIn(field, fields)
    
    def test_store(self):
        ussd = USSDAccess.objects.create(aggregator="blah blah",interviewer_id=1)
        self.failUnless(ussd.intervieweraccess_ptr_id)
        self.failUnless(ussd.aggregator)

    def test_content(self):
        aggregator = USSDAccess.objects.get(aggregator="Dummy")
        self.assertEqual(aggregator.aggregator,'Dummy')
        self.assertEqual(len(aggregator.aggregator),5)

class ODKAccessTest(TestCase):

    def test_fields(self):
        odk_access = ODKAccess()
        fields = [str(item.attname) for item in odk_access._meta.fields]
        self.assertEqual(10, len(fields))
        for field in ['intervieweraccess_ptr_id', 'odk_token']:
            self.assertIn(field, fields)

    def test_store(self):
        interviewer = Interviewer.objects.create(name="Interviewer")
        odk_access = ODKAccess.objects.create(odk_token="rajesh",user_identifier="identifier name", reponse_timeout="1", interviewer=interviewer,
                                             duration='5')
        self.failUnless(odk_access.intervieweraccess_ptr_id)
        self.failUnless(odk_access.odk_token)

    def setUp(self):
        ODKAccess.objects.create(odk_token="Dummy",interviewer_id=1)

    def test_content(self):
        odk_token = ODKAccess.objects.get(odk_token="Dummy")
        self.assertEqual(odk_token.odk_token,'Dummy')
        self.assertEqual(len(odk_token.odk_token),5)