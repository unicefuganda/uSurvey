from django.test import TestCase
from datetime import datetime, date
from survey.models.locations import *
from survey.forms.interviewer import *
from survey.models import EnumerationArea, Survey
from survey.models.backend import Backend


class InvestigatorFormTest(TestCase):

    def setUp(self):
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.district = LocationType.objects.create(
            name='District', slug='district', parent=self.country)
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(
            name="Kampala", type=self.district, parent=self.uganda)
        self.location = self.kampala
        self.survey = Survey.objects.create(name="hoho")
        self.backend = Backend.objects.create(name='something')
        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.kampala)
        self.investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)

    def test_valid(self):
        survey_allocation = SurveyAllocation.objects.create(interviewer=self.investigator, survey=self.survey, allocation_ea=self.ea, stage=2,
                                                            status=0)
        form_data = {
            'name': 'Rajini',
            'ea': self.ea,
            'gender': '1',
            'level_of_education': 'Primary',
            'language': 'English',
                        'weights': 0,
                        'survey': self.survey,
                        'date_of_birth': date(1980, 05, 01)
        }
        investigator_form = InterviewerForm(form_data)
        self.assertFalse(investigator_form.is_valid())

    def test_invalid(self):
        form_data = {
            'name': 'Rajini',
            'ea': self.ea,
            'gender': '1',
            'level_of_education': 'Primary',
            'language': 'English',
                        'weights': 0,
                        'survey': self.survey,
                        'date_of_birth': date(1980, 05, 01)
        }
        keys = form_data.keys()
        # there's a default value for Male so it is valid even if it is not
        # provided.
        keys.remove('gender')
        for key in keys:
            modified_form_data = dict(form_data.copy())
            modified_form_data[key] = None
            investigator_form = InterviewerForm(modified_form_data)
            self.assertFalse(investigator_form.is_valid())
