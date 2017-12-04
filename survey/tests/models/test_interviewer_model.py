from django.test import TestCase
from datetime import datetime, timedelta
from django import forms
from survey.models import *
from survey.models.interviewer import *
from survey.interviewer_configs import *
from survey.tests.models.survey_base_test import SurveyBaseTest


class InterviewerTest(SurveyBaseTest):

    # def test_fields(self):
    #     ss_content = Interviewer()
    #     fields = [str(item.attname) for item in ss_content._meta.fields]
    #     self.assertEqual(11, len(fields))
    #     for field in ['id','created','modified','name','gender','date_of_birth',
    #                   'level_of_education','is_blocked','ea_id','language','weights']:
    #         self.assertIn(field, fields)
    #
    # def test_store(self):
    #     ea = EnumerationArea.objects.create(name="Kampala EA A")
    #     investigator = Interviewer.objects.create(name="Investigator",
    #                                               ea=ea,
    #                                               gender='1', level_of_education='Primary',
    #                                               language='Eglish', weights=0)
    #     survey = Survey.objects.create(
    #         name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
    #     batch = Batch.objects.create(order=1)
    #     self.failUnless(batch.id)
    #     self.failUnless(ea.id)
    #     self.failUnless(survey.id)
    #
    # def setUp(self):
    #     Interviewer.objects.create(name="Dummy")
    #
    # def test_name(self):
    #     name = Interviewer.objects.get(name="Dummy")
    #     self.assertEqual(name.name,'Dummy')
    #     self.assertEqual(len(name.name),5)
    #
    def test_unicode_text(self):
        itr = Interviewer.objects.create(name="abcd name")
        self.assertEqual(itr.name, str(itr))

    def test_validate_age(self):
        self.assertRaises(forms.ValidationError, validate_min_date_of_birth, datetime.now())
        older = datetime.now() - timedelta(days=(365 * (INTERVIEWER_MAX_AGE + 4)))
        self.assertRaises(forms.ValidationError, validate_max_date_of_birth, older)

    def test_attributes(self):
        self.assertEquals(self.interviewer.present_interviews, 1)
        # since at list 1 interview exists for it
        self.assertTrue(self.interviewer.completed_batch_or_survey(self.survey, self.qset))
        self.assertIn(self.ea.locations.first(), self.interviewer.locations_in_hierarchy())
        self.assertEquals(InterviewerAccess.objects.filter(interviewer=self.interviewer,
                                                       user_identifier__in=self.interviewer.access_ids).count(),
                      len(self.interviewer.access_ids))


    """ 119-123, 130, 134, 138, 143, 197-202, 209-210, 213, 240, 246, 252-259"""



class SurveyAllocationTest(TestCase):

    def test_unicode_text(self):
        self.survey = Survey.objects.create(name="sai",has_sampling=True,sample_size=1)
        self.interviewer = Interviewer.objects.create(name="raju",gender="male",is_blocked=True,weights=20)
        self.enumerationarea = EnumerationArea.objects.create(name="anushka")
        sua = SurveyAllocation.objects.create(status=1,allocation_ea_id=self.enumerationarea.id,interviewer_id=self.interviewer.id,survey_id=self.survey.id)
        self.assertEqual(sua.allocation_ea.name, str(sua))