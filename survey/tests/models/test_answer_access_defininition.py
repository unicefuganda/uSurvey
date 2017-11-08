from survey.models import AnswerAccessDefinition, USSDAccess, ODKAccess, WebAccess, Answer
from survey.tests.base_test import BaseTest


class TestAnswerAccessDefinition(BaseTest):

    def test_reload_answer_access(self):
        AnswerAccessDefinition.objects.all().delete()
        self.assertEquals(AnswerAccessDefinition.objects.count(), 0)
        AnswerAccessDefinition.reload_answer_categories()
        self.assertTrue(AnswerAccessDefinition.objects.count() > 0)
        # chech for each access type has an entry
        channels = [USSDAccess.choice_name(), ODKAccess.choice_name(), WebAccess.choice_name()]
        allowed_channels = AnswerAccessDefinition.access_channels()
        for channel in allowed_channels:
            self.assertIn(channel, allowed_channels)
            self.assertTrue(len(AnswerAccessDefinition.answer_types(channel)) > 0)
        answer_types = Answer.answer_types()
        for answer_type in answer_types:
            self.assertIn(answer_type, AnswerAccessDefinition.answer_types())
