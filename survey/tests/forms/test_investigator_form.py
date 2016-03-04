from django.test import TestCase
from datetime import datetime, date
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models.locations import *
from survey.forms.interviewer import *
from survey.models import EnumerationArea, Survey
from survey.models.backend import Backend


class InvestigatorFormTest(TestCase):

    def setUp(self):
        self.country = LocationType.objects.create(name='Country',slug='country')
        self.district = LocationType.objects.create(name='District',slug='district', parent=self.country)
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(name="Kampala", type=self.district, parent=self.uganda)
        self.location = self.kampala
        self.survey = Survey.objects.create(name="hoho")
        self.backend = Backend.objects.create(name='something')
        self.ea = EnumerationArea.objects.create(name="EA2")
        self.ea.locations.add(self.kampala)

    # def test_valid(self):
    #     # survey_allocation = SurveyAllocation.objects.create(interviewer=self.investigator,survey=self.survey,allocation_ea=self.ea,stage=2,
    #     #                                                     status=0)
    #     form_data = {
    #                     'name': 'Rajini',
    #                     'ea':self.ea.id,
    #                     'gender':'1',
    #                     'level_of_education':'Primary',
    #                     'language':'English',
    #                     'weights':0,
    #                     'survey':self.survey.id,
    #                     'date_of_birth':date(1980, 05, 01)
    #                 }
    #     investigator_form = InterviewerForm(form_data)
    #     self.assertTrue(investigator_form.is_valid())
    #     investigator = investigator_form.save()
    #     self.failUnless(investigator.id)
    #     self.assertNotEqual(investigator.id, form_data['id'])

    # def test_invalid(self):
    #     form_data = {
    #                     'name': 'Rajini',
    #                     'mobile_number': '987654321',
    #                     'male': 't',
    #                     'age': '20',
    #                     'level_of_education': 'Primary',
    #                     'language': 'Luganda',
    #                     'ea': self.ea.id,
    #                     'confirm_mobile_number': '987654321',
    #                     'backend': self.backend.pk,
    #                 }
    #     keys = form_data.keys()
    #     keys.remove('male')   # there's a default value for Male so it is valid even if it is not provided.
    #     for key in keys:
    #         modified_form_data = dict(form_data.copy())
    #         modified_form_data[key] = None
    #         investigator_form = InvestigatorForm(modified_form_data)
    #         self.assertFalse(investigator_form.is_valid())
    #
    # def test_confirm_mobile_number(self):
    #     form_data = {
    #                   'name': 'Rajini',
    #                   'mobile_number': '987654321',
    #                   'male': 't',
    #                   'age': '20',
    #                   'level_of_education': 'Primary',
    #                   'language': 'Luganda',
    #                   'ea': self.ea.id,
    #                   'confirm_mobile_number': '123456789',
    #                   'backend': self.backend.pk,
    #               }
    #     form_data = dict(form_data.copy())
    #     investigator_form = InvestigatorForm(data=form_data)
    #     self.assertFalse(investigator_form.is_valid())
    #
    #     form_data['confirm_mobile_number'] = form_data['mobile_number']
    #     investigator_form = InvestigatorForm(form_data)
    #     self.assertTrue(investigator_form.is_valid())
    #
    # def test_mobile_number_is_of_length_9(self):
    #     number_of_length_10='0123456789'
    #     form_data = {
    #                   'name': 'Rajini',
    #                   'mobile_number': number_of_length_10,
    #                   'male': 't',
    #                   'age': '20',
    #                   'level_of_education': 'Primary',
    #                   'language': 'Luganda',
    #                   'ea': self.ea.id,
    #                   'confirm_mobile_number': number_of_length_10,
    #                   'backend': self.backend.pk,
    #               }
    #     form_data = dict(form_data.copy())
    #     investigator_form = InvestigatorForm(data=form_data)
    #     self.assertFalse(investigator_form.is_valid())
    #     self.assertEquals(len(investigator_form.errors),1)
    #     self.assertTrue(investigator_form.errors.has_key('mobile_number'))
    #
    # def test_age_is_between_18_and_50(self):
    #     form_data = {
    #                   'name': 'Rajini',
    #                   'mobile_number': '123456789',
    #                   'male': 't',
    #                   'age': '20',
    #                   'level_of_education': 'Primary',
    #                   'language': 'Luganda',
    #                   'ea': self.ea.id,
    #                   'confirm_mobile_number': '123456789',
    #                   'backend': self.backend.pk,
    #               }
    #     form_data = dict(form_data.copy())
    #     investigator_form = InvestigatorForm(data=form_data)
    #     self.assertTrue(investigator_form.is_valid())
    #
    #     form_data['age'] = 17
    #     investigator_form = InvestigatorForm(data=form_data)
    #     self.assertFalse(investigator_form.is_valid())
    #     self.assertEquals(len(investigator_form.errors),1)
    #     self.assertTrue(investigator_form.errors.has_key('age'))
    #
    #
    #     form_data['age'] = 51
    #     investigator_form = InvestigatorForm(data=form_data)
    #     self.assertFalse(investigator_form.is_valid())
    #     self.assertEquals(len(investigator_form.errors),1)
    #     self.assertTrue(investigator_form.errors.has_key('age'))
    #
    #
    # def test_langugage_and_level_of_education_validity(self):
    #     for key in ['language', 'level_of_education']:
    #         investigator = InvestigatorForm({key: 'something'})
    #         self.assertEqual(investigator.errors[key][0], 'Select a valid choice. something is not one of the available choices.')