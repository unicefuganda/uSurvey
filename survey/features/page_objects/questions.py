from survey.features.page_objects.base import PageObject
from lettuce.django import django_url

class QuestionsListPage(PageObject):
    def __init__(self, browser, batch):
        self.browser = browser
        self.batch = batch
        self.url = '/batches/%d/questions/' % batch.id

    def validate_fields(self):
        self.is_text_present('%s Question'% self.batch.name.capitalize())
        self.is_text_present('Question')
        self.is_text_present('Question Type')
        self.is_text_present('Actions')

    def validate_pagination(self):
        self.browser.click_link_by_text("2")

