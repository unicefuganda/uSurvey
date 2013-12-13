from django.test import TestCase
from survey.forms.aboutus_form import AboutUsForm


class AboutUsFormTest(TestCase):
    def test_valid(self):
        form_data = {
            'content': 'description goes here',
        }
        aboutus_form = AboutUsForm(form_data)
        self.assertTrue(aboutus_form.is_valid())

    def test_invalid(self):
        form_data = {
            'content': '',
        }
        aboutus_form = AboutUsForm(form_data)
        self.assertFalse(aboutus_form.is_valid())
        self.assertEqual(['This field is required.'], aboutus_form .errors['content'])