from django.test import TestCase
from survey.models import RespondentGroup, ParameterTemplate, GroupTestArgument, RespondentGroupCondition


class RespondentTest(TestCase):

    def setUp(self):
        self.rsg = RespondentGroup.objects.create(name="Dummy",description="description")
        self.pt = ParameterTemplate.objects.create(identifier='id_1',text='age',answer_type='text',templatequestion_ptr_id=1)

    def test_fields(self):
        rsg = RespondentGroup()
        fields = [str(item.attname) for item in rsg._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'description']:
            self.assertIn(field, fields)

    def test_store(self):
        rsg = RespondentGroup.objects.create(name='abc',description="blah blah")
        self.failUnless(rsg.id)
        self.failUnless(rsg.name)
    
    def test_name(self):
        name = RespondentGroup.objects.get(name="Dummy")
        self.assertEqual(name.name,'Dummy')
        self.assertEqual(len(str(name.name)),5)

    def test_unicode_text(self):
        self.assertEqual(self.pt.identifier, str(self.pt))
        self.assertEqual(self.rsg.name, str(self.rsg.name))

class RespondentGroupTest(TestCase):
    
    def test_unicode_text(self):
        rg = RespondentGroup.objects.create(name="group name")
        self.assertEqual(rg.name, str(rg))
    
    def test_fields(self):
        rgroup = RespondentGroup()
        fields = [str(item.attname) for item in rgroup._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'description']:
            self.assertIn(field, fields)

    def test_store(self):
        rgroup = RespondentGroup.objects.create(name="Respondentgroup", description="sample description")
        self.failUnless(rgroup.id)
        self.failUnless(rgroup.name)
        self.failUnless(rgroup.description)
    
    def setUp(self):
        RespondentGroup.objects.create(name="dunn",description="description")

    def test_name(self):
        name = RespondentGroup.objects.get(name="dunn")
        description = RespondentGroup.objects.get(description="description")
        self.assertEqual(name.name,'dunn')
        self.assertEqual(len(name.name),4)
        self.assertEqual(description.description,'description')
        self.assertEqual(len(description.description),11)

class GroupTestArgumentTest(TestCase):
    
    def setUp(self):
        self.rsg = RespondentGroup.objects.create(name="Dummy",description="description")
        self.pt = ParameterTemplate.objects.create(identifier='id_1', text='age', answer_type='text', templatequestion_ptr_id=1)
        self.rgc = RespondentGroupCondition.objects.create(respondent_group=self.rsg, test_question=self.pt, validation_test="validtest")
        self.reds = GroupTestArgument.objects.create(group_condition=self.rgc, position="1", param="testparam")

    def test_unicode_text(self):
        dt = GroupTestArgument.objects.create(group_condition=self.rgc, position="1", param="testparam")
        self.assertEqual(dt.param, str(dt))

    def test_fields(self):
        gta = GroupTestArgument()
        fields = [str(item.attname) for item in gta._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created', 'modified', 'position', 'param', 'group_condition_id']:
            self.assertIn(field, fields)

    def test_store(self):
        td = GroupTestArgument.objects.create(group_condition=self.rgc, position="1", param="testparam")
        self.failUnless(td.id)
        self.failUnless(td.group_condition)
        self.failUnless(td.position)
        self.failUnless(td.param)