from survey.models import (AnswerAccessDefinition, USSDAccess, ODKAccess, WebAccess, Answer,
                           VideoAnswer, AudioAnswer, ImageAnswer)
from survey.tests.base_test import BaseTest


class TestAnswerAccessDefinition(BaseTest):

    def test_reload_answer_access(self):
        AnswerAccessDefinition.objects.all().delete()
        self.assertEquals(AnswerAccessDefinition.objects.count(), 0)
        AnswerAccessDefinition.reload_answer_categories()
        self.assertTrue(AnswerAccessDefinition.objects.count() > 0)
        # chech for each access type has an entry
        channels = [USSDAccess.choice_name(), ODKAccess.choice_name(), WebAccess.choice_name()]
        allowed_channels = AnswerAccessDefinition.objects.values_list('channel', flat=True)
        for channel in channels:
            self.assertIn(channel, allowed_channels)
            self.assertTrue(len(AnswerAccessDefinition.answer_types(channel)) > 0)
        answer_types = Answer.answer_types()
        for answer_type in [VideoAnswer, AudioAnswer, ImageAnswer]:
            self.assertNotIn(answer_type.choice_name(), AnswerAccessDefinition.answer_types(USSDAccess.choice_name()))

