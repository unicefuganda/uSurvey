from django.test import TestCase
from survey.models import AboutUs


class AboutUsContentTest(TestCase):

    def test_fields(self):
        about_us_content = AboutUs()
        fields = [str(item.attname) for item in about_us_content._meta.fields]
        self.assertEqual(4, len(fields))
        for field in ['id', 'created', 'modified', 'content']:
            self.assertIn(field, fields)

    def test_store(self):
        about_us_content = AboutUs.objects.create(content="blah blah")
        self.failUnless(about_us_content.id)
        self.failUnless(about_us_content.content)
