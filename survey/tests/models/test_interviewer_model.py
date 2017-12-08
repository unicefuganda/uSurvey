from django.test import TestCase
from datetime import datetime, timedelta
from django import forms
from survey.models import *
from survey.models.interviewer import *
from survey.interviewer_configs import *
from survey.tests.models.survey_base_test import SurveyBaseTest


class InterviewerTest(SurveyBaseTest):

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

    def test_get_allocation_details(self):
        self.assertEquals(SurveyAllocation.get_allocation(self.interviewer), self.survey)


class SurveyAllocationTest(TestCase):

    def test_unicode_text(self):
        self.survey = Survey.objects.create(name="sai",has_sampling=True,sample_size=1)
        self.interviewer = Interviewer.objects.create(name="raju",gender="male",is_blocked=True,weights=20)
        self.enumerationarea = EnumerationArea.objects.create(name="anushka")
        sua = SurveyAllocation.objects.create(status=1, allocation_ea_id=self.enumerationarea.id,
                                              interviewer_id=self.interviewer.id,survey_id=self.survey.id)
        self.assertEqual(sua.allocation_ea.name, str(sua))