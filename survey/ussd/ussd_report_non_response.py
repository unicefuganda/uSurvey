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
        self.set_question()
        self.currently_open_batch = None
        self.set_currently_open_batch()

    def set_currently_open_batch(self):
        if self.household:
            self.currently_open_batch = Batch.currently_open_for(self.household.location)

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
            if self.household.has_some_members_who_completed():
                self.select_member_or_process_member_question(answer)
            else:
                self.paginates_or_process_household_question(answer)
        else:
            self.select_household(answer, non_response_reporting=True)
            self.render_questions_or_select_member()

    def render_questions_or_select_member(self, answer=None):
        if self.household.all_members_non_completed():
            self.render_non_response_question(answer, for_household=True)
        else:
            self.render_household_members_list()

    def process_non_response_answer(self, answer):
        if not self.question or self.is_pagination_option(answer):
            self.render_non_response_question(answer)
        else:
            self.validate_question_and_save_non_response_answer(answer)

    def render_member_non_response_question(self, answer):
        self.render_non_response_question(answer, for_household=False)

    def render_non_response_question(self, answer, for_household=True):
        order = 1 if for_household else 2
        string_interpolation = (self.household.uid, self.household.get_head().surname) if for_household else self.household_member.surname
        self.set_current_page(answer)
        self.question = Question.objects.filter(group__name="NON_RESPONSE", order=order)[0]
        self.set_in_session("QUESTION", self.question)
        page = self.get_from_session('PAGE')
        self.responseString += self.question.to_ussd(page) % string_interpolation

    def validate_question_and_save_non_response_answer(self, answer):
        question_option = self.validate_question_option(answer)
        if question_option:
            self.save_answer_and_clear_question(question_option)
            self.render_household_list_or_completion_message()
        else:
            self.render_non_response_question(answer)

    def save_answer_and_clear_question(self, question_option, household=True):
        answer_dict = {'investigator': self.investigator, 'answer': question_option, 'question': self.question,
                       'batch': self.currently_open_batch, 'household':self.household}
        self.save_answer(answer_dict, household)
        self.clear_cached_sessions(household)

    def save_answer(self, answer_dict, household):
        if not household:
            answer_dict['householdmember'] = self.household_member
        MultiChoiceAnswer.objects.create(**answer_dict)

    def clear_cached_sessions(self, household):
        self.set_in_session("QUESTION", None)
        self.set_in_session("HOUSEHOLD_MEMBER", None)
        if household:
            self.set_in_session("HOUSEHOLD", None)

    def validate_question_option(self, answer):
        question_option = self.question.get_option(answer, self.investigator)
        if question_option:
            return question_option
        else:
            self.responseString = "INVALID ANSWER: "

    def select_household_member(self, answer):
        try:
            answer = int(answer)
            self.household_member = self.household.get_non_complete_members()[answer - 1]
            self.set_in_session('HOUSEHOLD_MEMBER', self.household_member)
            return
        except (ValueError, IndexError) as e:
            self.responseString += "INVALID SELECTION: "
            self.render_household_members_list()

    def process_member_non_response_answer(self, answer):
        question_option = self.question.get_option(answer, self.investigator)
        if not question_option:
            self.responseString = "INVALID ANSWER: "
            self.render_member_non_response_question(answer)
        else:
            self.save_answer_and_clear_question(question_option, household=False)
            self.render_members_or_households_or_completion_message()

    def render_members_or_households_or_completion_message(self):
        if self.household.members_have_completed_non_response(self.currently_open_batch):
            self.save_answer_and_clear_question(question_option=None, household=True)
            self.render_household_list_or_completion_message()
        else:
            self.render_household_members_list()

    def select_member_or_paginate_member_list(self, answer):
        if self.is_pagination_option(answer):
            self.set_current_page(answer)
            self.render_household_members_list()
        else:
            self.select_household_member(answer)

    def display_question_or_answer_question(self, answer):
        if self.question and not self.is_pagination_option(answer):
            self.process_member_non_response_answer(answer)
        else:
            self.render_member_non_response_question(answer)

    def select_member_or_process_member_question(self, answer):
        if not self.household_member:
            self.select_member_or_paginate_member_list(answer)
        if self.household_member:
            self.display_question_or_answer_question(answer)

    def paginates_or_process_household_question(self, answer):
        if self.question and not self.is_pagination_option(answer):
            self.process_non_response_answer(answer)
        else:
            self.render_non_response_question(answer)

    def render_household_list_or_completion_message(self):
        if self.investigator.completed_non_response_reporting(open_survey=self.currently_open_batch.survey):
            self.responseString = self.MESSAGES['NON_RESPONSE_COMPLETION']
        else:
            self.get_household_list(non_response_reporting=True)


