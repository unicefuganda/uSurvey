from django.test import TestCase
from survey.forms.locations import LocationTypeForm
from rapidsms.contrib.locations.models import Location, LocationType

class LocationTypeFormTest(TestCase):
    def test_valid(self):
        form_data = {'name': 'some name say country'}
        type_form = LocationTypeForm(form_data)
        type_form.is_valid()
        print type_form.errors
        self.assertTrue(type_form.is_valid())

    def test_name_is_required(self):
        type_form = LocationTypeForm({'name':''})
        self.assertFalse(type_form.is_valid())
        self.assertEquals(type_form.errors['name'], ['This field is required.'])

    def test_form_should_be_invalid_if_name_already_exists(self):
        a_type = LocationType.objects.create(name='type')
        type_form = LocationTypeForm({'name':a_type.name})
        self.assertFalse(type_form.is_valid())
        message = "%s already exists"% a_type.name
        self.assertEquals(type_form.errors['name'], [message])
