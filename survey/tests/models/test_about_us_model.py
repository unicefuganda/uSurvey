from django.test import TestCase
from survey.models import AboutUs,SuccessStories


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
    def setUp(self):
        AboutUs.objects.create(content="Dummy")
    def test_content(self):
        content = AboutUs.objects.get(content="Dummy")
        self.assertEqual(content.content,'Dummy')
        self.assertEqual(len(content.content),5)        

class SuccessStoriesTest(TestCase):
    def setUp(self):
        SuccessStories.objects.create(name="India", content="Hyderabad")
    def test_success(self):
        name = SuccessStories.objects.get(name="India")
        content = SuccessStories.objects.get(content="Hyderabad")
        self.assertEqual(name.name,'India')
        self.assertEqual(content.content,'Hyderabad')
        self.assertEqual(len(name.name),5)