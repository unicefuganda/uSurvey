from django.test import TestCase
from survey.models import ResponseValidation, TestArgument, TextArgument
from survey.models.response_validation import NumberArgument, DateArgument
class ResponseValidationTest(TestCase):

    def test_fields(self):
        rvt = ResponseValidation()
        fields = [str(item.attname) for item in rvt._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'validation_test','constraint_message']:
            self.assertIn(field, fields)

    def test_store(self):
        rv = ResponseValidation.objects.create(validation_test="blah",constraint_message="message")
        self.failUnless(rv.id)
        self.failUnless(rv.validation_test)
        self.failUnless(rv.constraint_message)
    
    def setUp(self):
        ResponseValidation.objects.create(validation_test="blah",constraint_message="message")
    
    def test_content(self):
        rv = ResponseValidation.objects.get(validation_test="blah",constraint_message="message")
        self.assertEqual(rv.validation_test,'blah')
        self.assertEqual(len(rv.validation_test),4)
        self.assertEqual(rv.constraint_message,'message')
        self.assertEqual(len(rv.constraint_message),7)
    def test_unicode_text(self):
        ivs = ResponseValidation.objects.create(validation_test="blah",constraint_message="message")
        self.assertNotEqual(ivs.validation_test, str(ivs))

class TestArgumentTest(TestCase):

    def test_fields(self):
        ta = TestArgument()
        fields = [str(item.attname) for item in ta._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'validation_id','position']:
            self.assertIn(field, fields)
    
    def test_store(self):
        self.respval = ResponseValidation.objects.create(validation_test="test",constraint_message="message")
        ta = TestArgument.objects.create(validation_id=self.respval.id,position=1)
        self.failUnless(ta.id)
        self.failUnless(ta.validation_id)
        self.failUnless(ta.position)

class TextArgumentTest(TestCase):

    def test_fields(self):
        tasd = TextArgument()
        fields = [str(item.attname) for item in tasd._meta.fields]
        self.assertEqual(7, len(fields))
        for field in ["testargument_ptr_id","param"]:
            self.assertIn(field, fields)

    def test_store(self):
        rv = TextArgument.objects.create(testargument_ptr_id=1,param="param",position=1)
        self.failUnless(rv.testargument_ptr_id)
        self.failUnless(rv.param)

    def test_content(self):
        rvs = TextArgument.objects.create(testargument_ptr_id=1,param="param",position=1)        
        self.assertEqual(rvs.param,'param')
        self.assertEqual(len(rvs.param),5)
    
    def test_unicode_text(self):
        ivs = TextArgument.objects.create(testargument_ptr_id=1,param="param",position=1)
        self.assertEqual(ivs.param, str(ivs))

class NumberArgumentTest(TestCase):

    def test_fields(self):
        na = NumberArgument()
        fields = [str(item.attname) for item in na._meta.fields]
        self.assertEqual(7, len(fields))
        for field in ["testargument_ptr_id","param"]:
            self.assertIn(field, fields)
    
    def test_store(self):
        na = NumberArgument.objects.create(testargument_ptr_id=1,param=1,position=1)
        self.failUnless(na.testargument_ptr_id)
        self.failUnless(na.param)

    def test_content(self):
        na = NumberArgument.objects.create(testargument_ptr_id=1,param=1,position=1)        

class DateArgumentTest(TestCase):

    def test_fields(self):
        na = DateArgument()
        fields = [str(item.attname) for item in na._meta.fields]
        self.assertEqual(7, len(fields))
        for field in ["testargument_ptr_id","param"]:
            self.assertIn(field, fields)

    def test_store(self):
        na = DateArgument.objects.create(testargument_ptr_id=1,param='1999-01-13',position=1)
        self.failUnless(na.testargument_ptr_id)
        self.failUnless(na.param)