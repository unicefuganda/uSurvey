from survey.features.page_objects.base import PageObject
from lettuce.django import django_url

class QuestionsListPage(PageObject):
    def __init__(self, browser, batch_id):
        self.browser = browser
        self.url = '/batches/%d/questions/' % batch_id

