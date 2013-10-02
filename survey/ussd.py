from django.core.cache import cache
from django.conf import settings
from survey.investigator_configs import *
from survey.models import HouseholdHead
from survey.models.random_household_selection import RandomHouseHoldSelection


class USSDBase(object):
    MESSAGES = {
        'SUCCESS_MESSAGE': "This survey has come to an end. Your responses have been received. Thank you.",
        'BATCH_5_MIN_TIMEDOUT_MESSAGE': "This batch is already completed and 5 minutes have passed. You may no longer retake it.",
        'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for this survey",
        'WELCOME_TEXT': "Welcome %s to the survey.",
        'HOUSEHOLD_LIST': "Please select a household from the list",
        'MEMBERS_LIST': "Please select a member from the list",
        'SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS': "The survey is now complete. Please collect your salary from the district coordinator.",
        'RETAKE_SURVEY': "You have already completed this household. Would you like to start again?\n1: Yes\n2: No",
        'NO_HOUSEHOLDS': "Sorry, you have no households registered.",
        'NO_OPEN_BATCH': "Sorry, there are no open surveys currently.",
        'HOUSEHOLDS_COUNT_QUESTION': "How many households have you listed in your segment?",
        'HOUSEHOLD_SELECTION_SMS_MESSAGE': "Thank you. You will receive the household numbers selected for your segment",
        'HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE': "Count must be greater than %s. How many households have you listed in your segment?" % NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR,
        'MEMBER_SUCCESS_MESSAGE':"Thank you. Would you like to proceed to the next Household Member?\n1: Yes\n2: No",
        'HOUSEHOLD_COMPLETION_MESSAGE':"Thank you. You have completed this household. Would you like to retake this household?\n1: Yes\n2: No",
        'RESUME_MESSAGE':"Would you like to to resume with member question?\n1: Yes\n2: No",
    }

    ACTIONS = {
        'REQUEST': 'request',
        'END': 'end'
    }

    ANSWER = {
        'YES':"1",
        'NO':"2"
    }

    DEFAULT_SESSION_VARIABLES = {
        'PAGE': 1,
        'HOUSEHOLD': None,
        'HOUSEHOLD_MEMBER': None
    }

    HOUSEHOLD_LIST_OPTION = "00"

    TIMEOUT_MINUTES = 5

    def is_new_request(self):
        return self.request['response'] == 'false'


class USSD(USSDBase):
    def __init__(self, investigator, request):
        super(USSD, self).__init__()
        self.investigator = investigator
        self.request = request.dict()
        self.action = self.ACTIONS['REQUEST']
        self.responseString = ""
        self.household = None
        self.household_member = None
        self.current_member_is_done = False
        self.is_resuming_survey = False
        self.set_session()
        self.set_household()
        self.set_household_member()
        self.set_current_member_is_done()
        self.set_is_resuming_survey()
        self.clean_investigator_input()

    def set_household(self):
        household = self.get_from_session('HOUSEHOLD')
        if household:
            self.household = household

    def set_household_member(self):
        household_member = self.get_from_session('HOUSEHOLD_MEMBER')
        if household_member:
            self.household_member = household_member

    def set_current_member_is_done(self):
        if self.household_member:
            self.current_member_is_done = self.household_member.survey_completed()

    def set_is_resuming_survey(self):
        try:
            cache_resuming_session = self.get_from_session('IS_RESUMING')
            self.is_resuming_survey = cache_resuming_session
        except:
            pass

    def set_session(self):
        self.session_string = "SESSION-%s" % self.request['transactionId']
        if not cache.get(self.session_string):
            cache.set(self.session_string, self.DEFAULT_SESSION_VARIABLES)

    def get_from_session(self, key):
        return cache.get(self.session_string)[key]

    def set_in_session(self, key, value):
        session = cache.get(self.session_string)
        session[key] = value
        cache.set(self.session_string, session)

    def is_pagination_option(self, answer):
        return answer in getattr(settings, 'USSD_PAGINATION', None).values()

    def is_pagination(self, question, answer):
        pagination = False
        if question.is_multichoice():
            pagination = self.is_pagination_option(answer)
        if not pagination:
            self.set_in_session('PAGE', self.DEFAULT_SESSION_VARIABLES['PAGE'])
        return pagination

    def set_current_page(self, answer):
        current_page = self.get_from_session('PAGE')
        if answer == getattr(settings, 'USSD_PAGINATION', None).get('PREVIOUS'):
            current_page -= 1
        elif answer == getattr(settings, 'USSD_PAGINATION', None).get('NEXT'):
            current_page += 1
        self.set_in_session('PAGE', current_page)

    def question_present_in_cache(self, label):
        return self.question in self.investigator.get_from_cache(label)

    def reanswerable_question(self):
        return self.question_present_in_cache('REANSWER')

    def invalid_answered_question(self):
        return self.question_present_in_cache('INVALID_ANSWER')

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
            self.render_household_members_list()
        if answer == self.ANSWER['NO']:
            self.set_in_session('HOUSEHOLD', None)
            self.set_in_session('HOUSEHOLD_MEMBER', None)
            self.household = None
            self.render_households_list(answer)

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
                self.investigator.clear_interview_caches()
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

    def is_browsing_households_list(self, answer,list_option="00"):
        if answer == list_option or self.is_pagination_option(answer):
            self.set_current_page(answer)
            return True

    def select_household(self, answer):
        try:
            answer = int(answer)
            self.household = self.investigator.all_households()[answer - 1]
            self.set_in_session('HOUSEHOLD', self.household)
        except (ValueError, IndexError) as e:
            self.responseString += "INVALID SELECTION: "

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
            self.render_households_list(answer)
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
                    self.render_households_list(answer)
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

    def render_households_list(self, answer):
        if not self.household:
            page = self.get_from_session('PAGE')
            self.responseString += "%s\n%s" % (self.MESSAGES['HOUSEHOLD_LIST'], self.investigator.households_list(page))
        else:
            self.behave_like_new_request()
            self.render_survey()

    def render_household_members_list(self):
        page = self.get_from_session('PAGE')
        self.responseString += "%s\n%s" % (self.MESSAGES['MEMBERS_LIST'], self.household.members_list(page))

    def render_homepage(self):
        answer = self.request['ussdRequestString'].strip()
        if not answer and not self.is_active():
            self.render_welcome_text()
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

    def response(self):
        if self.investigator.has_open_batch():
            self.process_open_batch()
        else:
            self.show_message_for_no_open_batch()
        return {'action': self.action, 'responseString': self.responseString}

    def clean_investigator_input(self):
        if self.is_new_request():
            self.request['ussdRequestString'] = ''

    def behave_like_new_request(self):
        self.request['ussdRequestString'] = ""
        self.request['response'] = 'false'

    def is_invalid_response(self):
        return "INVALID SELECTION: " in self.responseString

    @classmethod
    def investigator_not_registered_response(self):
        return {'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['USER_NOT_REGISTERED']}


class HouseHoldSelection(USSDBase):
    def __init__(self, mobile_number, request):
        super(HouseHoldSelection, self).__init__()
        self.mobile_number = mobile_number
        self.request = request

    def randomly_select_households(self):
        no_of_households = int(self.request['ussdRequestString'].strip())
        if no_of_households >= NUMBER_OF_HOUSEHOLD_PER_INVESTIGATOR:
            RandomHouseHoldSelection.objects.get_or_create(mobile_number=self.mobile_number)[0].generate(
                no_of_households=no_of_households)
            return {'action': self.ACTIONS['END'], 'responseString': self.MESSAGES['HOUSEHOLD_SELECTION_SMS_MESSAGE']}
        else:
            return {'action': self.ACTIONS['REQUEST'],
                    'responseString': self.MESSAGES['HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE']}

    def response(self):
        if self.is_new_request():
            return {'action': self.ACTIONS['REQUEST'], 'responseString': self.MESSAGES['HOUSEHOLDS_COUNT_QUESTION']}
        else:
            return self.randomly_select_households()