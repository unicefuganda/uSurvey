from django.test import TestCase
from survey.forms.question_set import BatchForm
from survey.models.locations import *
from survey.models import EnumerationArea
from survey.models import Interviewer
from survey.models.access_channels import *
from survey.models.batch import Batch
from survey.models.surveys import Survey


class BatchFormTest(TestCase):
    
    def test_valid(self):
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.africa = Location.objects.create(name='Africa', type=self.country)        
        self.city_ea = EnumerationArea.objects.create(name="CITY EA")
        self.city_ea.locations.add(self.africa)
        self.investigator_1 = Interviewer.objects.create(name="Investigator",
                                                         ea=self.city_ea,
                                                         gender='1', level_of_education='Primary',
                                                         language='Eglish', weights=0)
        odk = ODKAccess.objects.create(interviewer=self.investigator_1, user_identifier='Test', is_active=True, reponse_timeout=1000,
                                       duration='H', odk_token='Test')
        form_data = {
            'name': 'Batch 1',
            'description': 'description goes here',
        }
        batch_form = BatchForm(form_data)
        self.assertFalse(batch_form.is_valid())

    def test_invalid(self):
        form_data = {
            'name': 'test',
            'description': 'description goes here',
        }
        batch_form = BatchForm(form_data)
        self.assertFalse(batch_form.is_valid())

    def test_field_required(self):
        data = {'name': '', 'description': ''}
        batch_form = BatchForm(data)
        self.assertFalse(batch_form.is_valid())
        self.assertEqual(['This field is required.'],
                         batch_form.errors['name'])

    def test_form_should_be_invalid_if_name_already_exists_on_the_same_survey(self):
        survey = Survey.objects.create(name="very fast")
        Batch.objects.create(survey=survey, name='Batch A',
                             description='description')
        form_data = {
            'name': 'Batch A',
            'description': 'description goes here',
        }
        batch_form = BatchForm(data=form_data, instance=Batch(survey=survey))
        self.assertFalse(batch_form.is_valid())