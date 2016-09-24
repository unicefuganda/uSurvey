from survey.models import Question, QuestionTemplate


class ExportQuestionsService:
    HEADERS = "Question Text; Group; Answer Type; Options"

    def __init__(self, batch=None):
        self.questions = self._get_questions(batch)
        print self.questions

    def _get_questions(self, batch):
        if batch:
            return batch.questions.all()
        return Question.objects.all()

    def formatted_responses(self):
        _formatted_responses = [self.HEADERS]
        for question in self.questions:
            if question.group:
                text = '%s, %s, %s' % (question.text.replace(
                    '\r\n', ' '), question.group.name, question.answer_type.upper())
                _formatted_responses.append(text)
                self._append_options(question, _formatted_responses)
        return _formatted_responses

    def _append_options(self, question, formatted_response):
        options = list(question.options.order_by('order'))
        if options:
            formatted_response[-1] += '; %s' % options.pop(0).text
            for option in options:
                formatted_response.append('; ; ; %s' % option.text)


def get_question_template_as_dump(questions):
    HEADERS = "Question Code,Question Text,Answer Type,Options,Group,Module"
    _formatted_responses = [HEADERS, ]
    map(lambda question:
        _formatted_responses.append('%s,%s,%s,%s,%s,%s' %
                                    (question.identifier, question.text.replace('\r\n', ' '), question.answer_type.upper(),
                                     '|'.join(
                                         [opt.to_text for opt in question.options.all()]),
                                     question.group.name, question.module.name)
                                    ), questions)
    return _formatted_responses


def get_batch_question_as_dump(questions):
    HEADERS = "Question Code,Question Text,Answer Type,Options,Logic,Group,Module"
    _formatted_responses = [HEADERS, ]
    map(lambda question:
        _formatted_responses.append('%s,%s,%s,%s,%s,%s,%s' %
                                    (question.identifier, question.text.replace('\r\n', ' '), question.answer_type.upper(),
                                     '|'.join(
                                         [opt.to_text for opt in question.options.all()]),
                                     get_logic_print(question), question.group.name, question.module.name)
                                    ), questions)
    return _formatted_responses


def get_logic_print(question):
    content = []
    for flow in question.flows.exclude(validation_test__isnull=True):
        # desc = flow.desc
        # if desc.startswith(flow.validation_test):
        #     desc = desc[len(flow.validation_test)+1:]
        next_question = flow.next_question
        identifier = ''
        if next_question:
            identifier = next_question.identifier
        content.append(' '.join([flow.validation_test, ' and '.join(flow.params_display()),  # this a gamble for between ques
                                 flow.desc or '', identifier]))
    return ' | '.join(content)
