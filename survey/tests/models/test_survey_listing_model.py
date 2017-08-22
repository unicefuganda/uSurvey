from django.test import TestCase
from survey.models.base import BaseModel
from survey.models.questions import Question, QuestionSet
from survey.models.interviews import Answer, MultiChoiceAnswer
from survey.models.surveys import Survey
from survey.models.interviews import Interview
from survey.models.survey_listing import ListingTemplate, ListingQuestion, RandomizationCriterion, CriterionTestArgument

class ListingTemplateTest(TestCase):
    def setUp(self):
        self.lt = ListingTemplate.objects.create(name='bla bla',description='dummy',questionset_ptr_id=1)
        
class ListingQuestionTest(TestCase):
    def setUp(self):
        self.lq = ListingQuestion.objects.create(identifier='id_1',text='age',answer_type='text',question_ptr_id=1)

class RandomizationCriterionTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha")
        # self.lq = ListingQuestion.objects.create(question_ptr_id=1,text='age',answer_type='text')
        self.lq = ListingQuestion.objects.create(qset_id=1)
        validation_test = RandomizationCriterion.objects.create("abc")

    def test_fields(self):
        r = RandomizationCriterion()
        fields = [str(item.attname) for item in r._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created','modified','validation_test','listing_question_id','survey_id']:
            self.assertIn(field, fields)

    def test_store(self):
        self.survey = Survey.objects.create(name="haha")
        self.lq = ListingQuestion.objects.create(identifier='id_1',text='age',answer_type='text',question_ptr_id=1)
        rr = RandomizationCriterion.objects.create(validation_test='abc',listing_question=self.lq,survey=self.survey)
        self.failUnless(rr.id)
        self.failUnless(rr.validation_test)
        self.failUnless(rr.listing_question)
        self.failUnless(ss.survey)
    def test_content(self):
        self.survey = Survey.objects.create(name="haha")
        self.lq = ListingQuestion.objects.create(identifier='id_1',text='age',answer_type='text',question_ptr_id=1)
        rr = RandomizationCriterion.objects.create(validation_test='abc',listing_question=self.lq,survey=self.survey)
        validation_test = RandomizationCriterion.objects.get(validation_test='abc')
        self.assertEqual(validation_test.validation_test,'abc')
        self.assertEqual(len(validation_test.validation_test),3)        

class CriterionTestArgumentTest(TestCase):
    def test_fields(self):
        cta = CriterionTestArgument()
        fields = [str(item.attname) for item in cta._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created','modified','position','param','test_condition_id']:
            self.assertIn(field, fields)
    def test_store(self):
        self.survey = Survey.objects.create(name="haha")
        self.lq = ListingQuestion.objects.create(identifier="id_1",text='age',answer_type='text',question_ptr_id=1)
        self.rc=RandomizationCriterion.objects.create(survey=self.survey,listing_question=self.lq,validation_test='abc')
        z=CriterionTestArgument.objects.create(position='1',param='testparam',test_condition=self.rc)
        self.failUnless(z.id)
        self.failUnless(z.position)
        self.failUnless(z.param)
        self.failUnless(z.test_condition_id)
    def test_content(self):
        self.survey = Survey.objects.create(name="haha")
        self.lq = ListingQuestion.objects.create(question_ptr_id=1,text='age',answer_type='text')
        self.rc=RandomizationCriterion.objects.create(survey=self.survey,listing_question=self.lq,validation_test='abc')
        z=CriterionTestArgument.objects.create(position="1",param='testparam',test_condition=self.rc)
        param = CriterionTestArgument.objects.create(param='testparam')
        self.assertEqual(param.param,'testparam')
        self.assertEqual(len(param.param),9)
    # def setUp(self):        
        # self.rc=RandomizationCriterion.objects.create(survey_id=1,listing_question_id=1,validation_test='abc')
        
    def test_unicode_text(self):
        pm = CriterionTestArgument.objects.create(test_condition_id=1,position="1",param="testparam")
        self.assertEqual(pm.param, str(pm))