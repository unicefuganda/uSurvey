# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.models import HouseholdHead
from survey.ussd.ussd import USSD


class USSDSurvey(USSD):
    def __init__(self, investigator, request):
        super(USSDSurvey, self).__init__(investigator, request)
        self.current_member_is_done = False
        self.is_resuming_survey = False
        self.is_registering_household = False
        self.set_session()
        self.set_household()
        self.set_household_member()
        self.set_current_member_is_done()
        self.set_is_resuming_survey()
        self.clean_investigator_input()


    def process_investigator_response(self, batch):
        answer = self.request['ussdRequestString'].strip()
        if not answer:
            return self.investigator.invalid_answer(self.question)
        if self.is_pagination(self.question, answer):
            self.set_current_page(answer)
        else:
            self.question = self.investigator.member_answered(self.question, self.household_member, answer, batch)

    def add_question_prefix(self):
        if self.reanswerable_question():
            self.responseString += "RECONFIRM: "
        if self.invalid_answered_question():
            self.responseString += "INVALID ANSWER: "

    def restart_survey(self):
        answer = self.request['ussdRequestString'].strip()
        if answer == self.ANSWER['YES']:
            self.set_in_session('HOUSEHOLD_MEMBER', None)
            if self.household.completed_currently_open_batches():
                for member in self.household.household_member.all():
                    member.mark_past_answers_as_old()

            self.render_household_members_list()
        if answer == self.ANSWER['NO']:
            self.set_in_session('HOUSEHOLD', None)
            self.set_in_session('HOUSEHOLD_MEMBER', None)
            self.household = None
            self.render_households_list()


        self.action = self.ACTIONS['REQUEST']

    def end_interview(self, batch):
        self.action = self.ACTIONS['END']

        if self.investigator.completed_open_surveys():
            self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS']
            self.investigator.clear_interview_caches()
        elif self.household_member.survey_completed():
            if self.current_member_is_done:
                self.restart_survey()
            else:
                self.action = self.ACTIONS['REQUEST']
                current_household = self.household
                self.investigator.clear_all_cache_fields_except('IS_REGISTERING_HOUSEHOLD')
                self.set_in_session('HOUSEHOLD', current_household)
                self.responseString = USSD.MESSAGES['MEMBER_SUCCESS_MESSAGE'] if not self.household.completed_currently_open_batches() else USSD.MESSAGES['HOUSEHOLD_COMPLETION_MESSAGE']
        elif self.household_member.last_question_answered() and \
                not self.household_member.can_retake_survey(batch=batch, minutes=self.TIMEOUT_MINUTES):
            self.responseString = USSD.MESSAGES['BATCH_5_MIN_TIMEDOUT_MESSAGE']
            self.investigator.clear_interview_caches()
        else:
            self.responseString = USSD.MESSAGES['SUCCESS_MESSAGE']
            self.investigator.clear_interview_caches()

    def render_survey_response(self, batch):
        if not self.question:
            self.end_interview(batch)
        else:
            page = self.get_from_session('PAGE')
            self.add_question_prefix()
            self.responseString += self.question.to_ussd(page)

    def render_survey(self):
        household_member = self.household_member

        current_batch = household_member.get_next_batch()

        if current_batch:
            self.question = household_member.next_question_in_order(current_batch)
            if not self.is_new_request():
                self.process_investigator_response(current_batch)

            self.render_survey_response(current_batch)
        else:
            self.end_interview(current_batch)

    def render_resume_message(self):
        self.responseString = self.MESSAGES['RESUME_MESSAGE']
        self.action = self.ACTIONS['REQUEST']
        self.set_in_session('IS_RESUMING', True)

    def render_welcome_text(self):
        if self.investigator.has_households():
            welcome_message = self.MESSAGES['WELCOME_TEXT'] % self.investigator.name
            self.responseString = "%s\n%s: Households list" % (welcome_message, self.HOUSEHOLD_LIST_OPTION)
        else:
            self.action = self.ACTIONS['END']
            self.responseString = self.MESSAGES['NO_HOUSEHOLDS']



    def select_household_member(self, answer):
        try:
            answer = int(answer)
            self.household_member = self.household.all_members()[answer - 1]
            self.set_in_session('HOUSEHOLD_MEMBER', self.household_member)
        except (ValueError, IndexError) as e:
            self.responseString += "INVALID SELECTION: "

    def show_member_question(self, household_member):
        self.household_member = household_member if not household_member.is_head() else HouseholdHead.objects.get(
            householdmember_ptr_id=household_member.id)
        self.set_in_session('HOUSEHOLD_MEMBER', household_member)
        self.set_in_session('HOUSEHOLD', household_member.household)
        self.behave_like_new_request()
        self.render_survey()

    def show_member_list(self, household_member):
        self.set_in_session('HOUSEHOLD', household_member.household)
        self.render_household_members_list()

    def resume_survey(self, answer, household_member):
        if self.ANSWER["YES"] == answer:
            self.show_member_question(household_member)
        elif self.ANSWER["NO"] == answer:
            self.show_member_list(household_member)

    def select_or_render_household(self, answer):
        if self.is_browsing_households_list(answer):
            self.render_households_list()
        else:
            if self.is_resuming_survey:
                last_answered = self.investigator.last_answered()
                household_member = last_answered.householdmember
                self.household = household_member.household
                self.resume_survey(answer, household_member)
                self.set_in_session('IS_RESUMING', False)
            else:
                self.select_household(answer)
                if self.is_invalid_response():
                    self.render_households_list()
                else:
                    self.request['ussdRequestString'] = ""
                    self.render_household_or_household_member(answer)

    def select_or_render_household_member(self, answer):
        if self.is_browsing_households_list(answer):
            self.render_household_members_list()
        else:
            if self.request['ussdRequestString'] == "":
                self.render_household_members_list()
            else:
                self.select_household_member(answer)
                self.behave_like_new_request()
                self.render_household_or_household_member(answer)

    def render_household_or_household_member(self, answer):
        if self.has_chosen_household():
            if not self.is_pagination_option(answer):
                self.set_in_session('PAGE', self.DEFAULT_SESSION_VARIABLES['PAGE'])
            if self.has_chosen_household_member():
                self.render_survey()
            else:
                self.select_or_render_household_member(answer)
        else:
            self.select_or_render_household(answer)

    def render_households_list(self):
        if not self.household:
            page = self.get_from_session('PAGE')
            self.responseString += "%s\n%s" % (self.MESSAGES['HOUSEHOLD_LIST'], self.investigator.households_list(page,registered=True))
        else:
            self.behave_like_new_request()
            self.render_survey()

    def render_household_members_list(self):
        page = self.get_from_session('PAGE')
        self.responseString += "%s\n%s" % (self.MESSAGES['MEMBERS_LIST'], self.household.members_list(page))

    def render_homepage(self):
        answer = self.request['ussdRequestString'].strip()
        if not self.investigator.has_households():
            self.action = self.ACTIONS['END']
            self.responseString = self.MESSAGES['NO_HOUSEHOLDS']
        elif not answer and self.is_active():
            self.render_resume_message()
        else:
            self.render_household_or_household_member(answer)

    def has_chosen_household(self):
        return self.household is not None

    def has_chosen_household_member(self):
        if self.has_chosen_household():
            return self.household_member is not None
        return False

    def is_active(self):
        return self.investigator.was_active_within(self.TIMEOUT_MINUTES)

    def process_open_batch(self):
        if self.has_chosen_household_member():
            self.render_survey()
        else:
            self.render_homepage()

    def show_message_for_no_open_batch(self):
        self.action = self.ACTIONS['END']
        self.responseString = self.MESSAGES['NO_OPEN_BATCH']

    def take_survey(self):
        if self.investigator.has_open_batch():
            self.process_open_batch()
        else:
            self.show_message_for_no_open_batch()

        return self.action, self.responseString

    def render_select_household(self):
        self.request['ussdRequestString']="00"
        self.take_survey()

    def render_welcome_or_resume(self):
        self.action = self.ACTIONS['REQUEST']
        if not self.is_active():
            self.responseString = self.MESSAGES['WELCOME_TEXT'] % self.investigator.name
            self.investigator.set_in_cache('IS_REGISTERING_HOUSEHOLD', None)
        else:
            self.render_resume_message()
        return self.action, self.responseString



    def behave_like_new_request(self):
        self.request['ussdRequestString'] = ""
        self.request['response'] = 'false'

    def is_invalid_response(self):
        return "INVALID SELECTION: " in self.responseString

    @classmethod
    def investigator_not_registered_response(self):
        return {'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['USER_NOT_REGISTERED']}

    def start(self):
        self.render_select_household()
        return self.action, self.responseString