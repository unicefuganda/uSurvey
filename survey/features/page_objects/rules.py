from survey.features.page_objects.base import PageObject


class AddLogicToBatchQuestionPage(PageObject):
    def __init__(self, browser, question):
        super(AddLogicToBatchQuestionPage, self).__init__(browser)
        self.question = question
        self.url = '/questions/%s/add_logic/' % question.id

    def validate_fields(self):
        fields = ['If %s' % self.question.text, 'Attribute', 'Then']

        f = ['condition','attribute','action','next_question','value','validate_with_option','validate_with_question','validate_with_value']
        [self.browser.find_by_name(item) for item in f]

        self.validate_fields_present(fields)
