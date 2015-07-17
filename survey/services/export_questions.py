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
                text = '%s; %s; %s' % (question.text.replace('\r\n', ' '), question.group.name, question.answer_type.upper())
                _formatted_responses.append(text)
                self._append_options(question, _formatted_responses)
        return _formatted_responses

    def _append_options(self, question, formatted_response):
        options = list(question.options.order_by('order'))
        if options:
            formatted_response[-1] += '; %s' % options.pop(0).text
            for option in options:
                formatted_response.append('; ; ; %s'%option.text)
                

def get_question_template_as_dump():
    HEADERS = "Question Text; Group; Module; Answer Type"
    questions = QuestionTemplate.objects.all()
    _formatted_responses = [HEADERS, ]
    map(lambda question:
         _formatted_responses.append('%s; %s; %s; %s' % 
        (question.text.replace('\r\n', ' '), question.group.name, question.module.name, question.answer_type.upper())
        ),
        questions)
    return _formatted_responses