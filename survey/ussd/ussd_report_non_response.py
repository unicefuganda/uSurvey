from survey.models import Question, MultiChoiceAnswer, Batch
from survey.ussd.ussd import USSD


class USSDReportNonResponse(USSD):

    def __init__(self, investigator, request):
        super(USSDReportNonResponse, self).__init__(investigator, request)
        self.question = None
        self.household_member = None
        self.household = None
        self.is_selecting_member = False
        self.set_household()
        self.set_household_member()
        self.set_is_selecting_member()
        self.set_question()

    def set_is_selecting_member(self):
        try:
            is_selecting_member = self.investigator.get_from_cache('is_selecting_member')
            if is_selecting_member is not None:
                self.is_selecting_member = is_selecting_member
        except KeyError:
            self.investigator.set_in_cache('is_selecting_member', False)

    def set_question(self):
        try:
            question = self.get_from_session('QUESTION')
            if question:
                self.question = question
        except KeyError:
            pass


    def start(self, answer):
        self.report_non_response(answer)
        return self.action, self.responseString

    def report_non_response(self, answer):
        if not self.household and self.is_browsing_households_list(answer):
            self.get_household_list(non_response_reporting=True)
        elif self.household:
            self.process_non_response_answer(answer)
        else:
            self.select_household(answer, non_response_reporting=True)
            self.render_non_response_question(answer)

    def process_non_response_answer(self, answer):
        if not self.question or self.is_pagination_option(answer):
            self.render_non_response_question(answer)
        else:
            self.validate_question_and_save_non_response_answer(answer)

    def render_non_response_question(self, answer):
        self.set_current_page(answer)
        self.question = Question.objects.filter(group__name="NON_RESPONSE")[0]
        self.set_in_session("QUESTION", self.question)
        page = self.get_from_session('PAGE')
        self.responseString = self.question.to_ussd(page) if self.question else None

    def validate_question_and_save_non_response_answer(self, answer):
        question_option = self.question.get_option(answer, self.investigator)
        if not question_option:
            self.render_non_response_question(answer)
            self.responseString = "INVALID ANSWER: " + self.responseString
        else:
            self.save_answer_and_clear_question(question_option)
            self.get_household_list(non_response_reporting=True)

    def save_answer_and_clear_question(self, question_option):
        currently_open_batch = Batch.currently_open_for(self.household.location)
        MultiChoiceAnswer.objects.create(investigator=self.investigator, answer=question_option,
                                      question=self.question, household=self.household, batch=currently_open_batch)
        self.set_in_session("QUESTION", None)