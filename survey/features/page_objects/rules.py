from survey.features.page_objects.base import PageObject


class AddLogicToBatchQuestionPage(PageObject):
    def __init__(self, browser, question):
        super(AddLogicToBatchQuestionPage, self).__init__(browser)
        self.question = question
        self.url = '/questions/%s/add_logic/' % question.id

    def validate_fields(self):
        fields = ['If %s' % self.question.text, 'Attribute', 'Then']

        self.validate_fields_present(fields)
