from django.test import TestCase
from survey.models import RespondentGroup, ParameterTemplate


class RespondentTest(TestCase):

    def setUp(self):
        self.rsg = RespondentGroup.objects.create(content="Dummy")
        self.pt = ParameterTemplate.objects.create(identifier='id_1',text='age',answer_type='text',templatequestion_ptr_id=1)

    def test_fields(self):
        rsg = RespondentGroup()
        fields = [str(item.attname) for item in rsg._meta.fields]
        self.assertEqual(4, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'description']:
            self.assertIn(field, fields)

    def test_store(self):
        rsg = RespondentGroup.objects.create(name='abc',description="blah blah")
        self.failUnless(rsg.id)
        self.failUnless(rsg.name)    
    
    def test_content(self):
        content = RespondentGroup.objects.get(name="Dummy")
        self.assertEqual(content.name,'Dummy')
        self.assertEqual(len(content.content),5)

    def test_unicode_text(self):
        self.assertEqual(self.pt.identifier, str(self.pt))
        self.assertEqual(self.rsg.name, str(self.rsg.name))