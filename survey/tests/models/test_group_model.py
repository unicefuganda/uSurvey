from django.test import TestCase
from survey.models import HouseholdMemberGroup, Question


class HouseholdMemberGroupTest(TestCase):

    def test_fields(self):
        group = HouseholdMemberGroup()
        fields = [str(item.attname) for item in group._meta.fields]
        self.assertEqual(5, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'order']:
            self.assertIn(field, fields)

    def test_store(self):
        hmg = HouseholdMemberGroup.objects.create(name="5 to 6 years")
        self.failUnless(hmg.id)
        self.failUnless(hmg.created)
        self.failUnless(hmg.modified)
        self.assertEquals("5 to 6 years", hmg.name)
        self.assertEquals(0, hmg.order)

    def test_knows_all_the_questions_associated(self):
        member_group = HouseholdMemberGroup.objects.create(name="5 to 6 years", order=0)
        another_member_group = HouseholdMemberGroup.objects.create(name="7 to 10 years", order=1)

        question_1 = Question.objects.create(identifier = "identifier1",
                                             text = "Question 1", answer_type = 'number',
                                             order = 1, subquestion = False, group = member_group)
        question_2 = Question.objects.create(identifier = "identifier1", text = "Question 2",
                                             answer_type = 'number', order = 2,
                                             subquestion = False, group = member_group)
        question_3 = Question.objects.create(identifier = "identifier1", text = "Question 3",
                                             answer_type = 'number', order = 1,
                                             subquestion = False, group = another_member_group)
        expected_member_questions = [question_1, question_2]
        unexpected_member_questions = [question_3]

        all_questions_for_group = member_group.all_questions()

        self.assertEqual(len(all_questions_for_group), 2)
        [self.assertIn(question, all_questions_for_group) for question in expected_member_questions]
        [self.assertNotIn(question, all_questions_for_group) for question in unexpected_member_questions]