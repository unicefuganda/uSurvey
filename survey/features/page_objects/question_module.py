from survey.features.page_objects.base import PageObject


class QuestionModuleList(PageObject):
    url = "/modules/"


class NewQuestionModule(PageObject):
    url = "/modules/new/"


class EditQuestionModulePage(PageObject):

    def __init__(self, browser, module):
        super(EditQuestionModulePage, self).__init__(browser)
        self.module = module
        self.url = '/modules/%s/edit/' % module.id