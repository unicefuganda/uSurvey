from django.test import TestCase
from survey.models.base import BaseModel
from survey.models.questions import Question, QuestionSet
from survey.models.interviews import Answer, MultiChoiceAnswer
from survey.models.surveys import Survey
from survey.models.interviews import Interview
from survey.models.survey_listing import ListingTemplate, ListingQuestion, RandomizationCriterion, CriterionTestArgument
from survey.models import *

class ListingTemplateTest(TestCase):
    def setUp(self):
        self.lt = ListingTemplate.objects.create(name='bla bla',description='dummy',questionset_ptr_id=1)
        
class ListingQuestionTest(TestCase):
    def setUp(self):
        self.lq = ListingQuestion.objects.create(identifier='id_1',text='age',answer_type='text',question_ptr_id=1)

class RandomizationCriterionTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(name="haha",has_sampling=True,sample_size=1)
        # self.lq = ListingQuestion.objects.create(question_ptr_id=1,text='age',answer_type='text')
        self.questionset = QuestionSet.objects.create(name="raja")
        self.question = Question.objects.create(text="text",answer_type="answer",mandatory=True,qset_id=1)
        # self.lq = ListingQuestion.objects.create(qset_id=1)
        validation_test = RandomizationCriterion.objects.create(validation_test="abc",listing_question_id=1,survey_id=1)

    def test_fields(self):
        r = RandomizationCriterion()
        fields = [str(item.attname) for item in r._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created','modified','validation_test','listing_question_id','survey_id']:
            self.assertIn(field, fields)

    def test_store(self):
        # self.survey = Survey.objects.create(name="ha")
        # self.lq = ListingQuestion.objects.create(identifier='id_1',text='age',answer_type='text',question_ptr_id=1)
        # rr = RandomizationCriterion.objects.create(validation_test='abc',listing_question=self.lq,survey=self.survey)
        self.survey = Survey.objects.create(name="say",has_sampling=True,sample_size=1)
        self.questionset = QuestionSet.objects.create(name="santh")
        self.question = Question.objects.create(text="text",answer_type="answer",mandatory=True,qset_id=2)
        rr = RandomizationCriterion.objects.create(validation_test="abc",listing_question_id=1,survey_id=1)
        self.failUnless(rr.id)
        self.failUnless(rr.validation_test)
        self.failUnless(rr.listing_question_id)
        self.failUnless(rr.survey_id)

    def test_content(self):
        # self.survey = Survey.objects.create(name="hey")
        # self.lq = ListingQuestion.objects.create(identifier='id_1',text='age',answer_type='text',question_ptr_id=1)
        # rr = RandomizationCriterion.objects.create(validation_test='abc',listing_question=self.lq,survey=self.survey)
        # validation_test = RandomizationCriterion.objects.get(validation_test='abc')
        self.survey = Survey.objects.create(name="see",has_sampling=True,sample_size=1)
        self.questionset = QuestionSet.objects.create(name="dil")
        self.question = Question.objects.create(text="text",answer_type="answer",mandatory=True,qset_id=self.questionset.id)
        validation_test = RandomizationCriterion.objects.create(validation_test="abc",listing_question_id=1,survey_id=1)
        self.assertEqual(validation_test.validation_test,'abc')
        self.assertEqual(len(validation_test.validation_test),3)        

class CriterionTestArgumentTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.create(name="raj",has_sampling=True,sample_size=1)
        self.questionset = QuestionSet.objects.create(name="raja")
        self.question = Question.objects.create(text="text",answer_type="answer",mandatory=True,qset_id=self.questionset.id)
        self.randomizationcriterion = RandomizationCriterion.objects.create(validation_test="validation",listing_question_id=1,survey_id=1)
        self.Criteriontestargument = CriterionTestArgument.objects.create(position=1,param='param',test_condition_id=1)
    
    def test_fields(self):
        cta = CriterionTestArgument()
        fields = [str(item.attname) for item in cta._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created','modified','position','param','test_condition_id']:
            self.assertIn(field, fields)
    def test_store(self):
        # self.survey = Survey.objects.create(name="hi")
        # self.lq = ListingQuestion.objects.create(identifier="id_1",text='age',answer_type='text',question_ptr_id=1)
        # self.rc=RandomizationCriterion.objects.create(survey=self.survey,listing_question=self.lq,validation_test='abc')
        # z=CriterionTestArgument.objects.create(position='1',param='testparam',test_condition=self.rc)
        self.survey = Survey.objects.create(name="sudhir",has_sampling=True,sample_size=1)
        self.questionset = QuestionSet.objects.create(name="raja")
        self.question = Question.objects.create(text="text",answer_type="answer",mandatory=True,qset_id=self.questionset.id)
        self.randomizationcriterion = RandomizationCriterion.objects.create(validation_test="validation",listing_question_id=1,survey_id=1)
        z = CriterionTestArgument.objects.create(position=1,param='param',test_condition_id=1)

        self.failUnless(z.id)
        self.failUnless(z.position)
        self.failUnless(z.param)
        self.failUnless(z.test_condition_id)
    def test_content(self):
        # self.survey = Survey.objects.create(name="ooh ")
        # self.lq = ListingQuestion.objects.create(question_ptr_id=1,text='age',answer_type='text')
        # self.rc=RandomizationCriterion.objects.create(survey=self.survey,listing_question=self.lq,validation_test='abc')
        # z=CriterionTestArgument.objects.create(position="1",param='testparam',test_condition=self.rc)
        # param = CriterionTestArgument.objects.create(param='testparam')
        self.survey = Survey.objects.create(name="rambabu",has_sampling=True,sample_size=1)
        self.questionset = QuestionSet.objects.create(name="raja")
        self.question = Question.objects.create(text="text",answer_type="answer",mandatory=True,qset_id=self.questionset.id)
        self.randomizationcriterion = RandomizationCriterion.objects.create(validation_test="validation",listing_question_id=1,survey_id=1)
        param = CriterionTestArgument.objects.create(position=1,param='param',test_condition_id=1)
        self.assertEqual(param.param,'param')
        self.assertEqual(len(param.param),5)
    # def setUp(self):        
        # self.rc=RandomizationCriterion.objects.create(survey_id=1,listing_question_id=1,validation_test='abc')
        
    def test_unicode_text(self):
        pm = CriterionTestArgument.objects.create(test_condition_id=1,position=1,param="testparam")
        self.assertEqual(pm.param, str(pm))