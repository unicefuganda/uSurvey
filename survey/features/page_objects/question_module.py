from survey.features.page_objects.base import PageObject


class QuestionModuleList(PageObject):
    url = "/modules/"


class NewQuestionModule(PageObject):
    url = "/modules/new/"