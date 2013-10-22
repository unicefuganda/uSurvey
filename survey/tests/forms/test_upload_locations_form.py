from django.test import TestCase
from survey.forms.upload_locations import UploadLocationForm


class UploadLocationFormTest(TestCase):
    def test_should_know_fields(self):
        upload_location_form = UploadLocationForm()

        fields = ['file']

        [self.assertIn(field, upload_location_form.fields) for field in fields]
