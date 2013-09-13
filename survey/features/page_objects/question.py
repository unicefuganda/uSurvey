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
        self.is_text_present('Question Group')
        # self.is_text_present('Actions')

    def validate_pagination(self):
        self.browser.click_link_by_text("2")

class AddQuestionPage(PageObject):
    def __init__(self, browser, batch):
        self.browser = browser
        self.batch = batch
        self.url = '/batches/%d/questions/new/' % batch.id

    def see_one_option_field(self, option):
        self.is_text_present(option)

    def see_option_add_and_remove_buttons(self, length):
        assert len(self.browser.find_by_css(".icon-plus")) == length
        assert len(self.browser.find_by_css(".icon-remove")) == length

    def option_not_present(self, option):
        assert not self.browser.is_text_present(option)
