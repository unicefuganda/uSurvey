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
        self.assertEqual(['This field is required.'],
                         aboutus_form .errors['content'])
class SuccessStoriesFormTest(TestCase):

    def test_valid(self):
        form_data = {
            'name' : 'blah',
            'content': 'description goes here',
        }
        success_form = SuccessStoriesForm(form_data)
        self.assertTrue(success_form.is_valid())

    def test_invalid(self):
        form_data = {
            'name': '',
            'content': '',
        }
        success_form = SuccessStoriesForm(form_data)
        self.assertFalse(success_form.is_valid())
        self.assertEqual(['This field is required.'],
                         success_form .errors['content'])