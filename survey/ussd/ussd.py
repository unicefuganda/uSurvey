# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from django.conf import settings
from django.core.cache import cache
from survey.models import Survey
from survey.ussd.base import USSDBase


class USSD(USSDBase):
    def __init__(self, investigator, request):
        self.investigator = investigator
        self.request = request.dict()
        self.action = self.ACTIONS['REQUEST']
        self.responseString = ""
        self.household = None
        self.household_member = None
        self.is_registering_household = True
        self.is_resuming_survey = False
        self.has_chosen_retake = False
        self.has_answered_retake = False
        self.can_retake_household = False
        self.question = None
        self.set_session()
        self.set_household()
        self.set_household_member()
        self.set_current_member_is_done()
        self.set_is_resuming_survey()
        self.set_has_chosen_retake()
        self.set_has_answered_retake()
        self.set_can_retake_household()
        self.clean_investigator_input()


    def set_attribute_from_session(self, key, attribute):
        try:
            attr_value = self.get_from_session(key)
            if attr_value:
                setattr(self, attribute, attr_value)
        except KeyError:
            pass

    def set_from_investigator_cache(self, key, attribute):
        try:
            attr_value = self.investigator.get_from_cache(key)
            if attr_value:
                setattr(self, attribute, attr_value)
        except KeyError:
            pass


    def set_household(self):
        self.set_attribute_from_session('HOUSEHOLD', 'household')

    def set_can_retake_household(self):
        self.set_attribute_from_session('CAN_RETAKE_HOUSEHOLD', 'can_retake_household')

    def set_household_member(self):
        self.set_attribute_from_session('HOUSEHOLD_MEMBER', 'household_member')

    def set_current_member_is_done(self):
        if self.household_member and (self.is_registering_household is False):
            self.current_member_is_done = self.household_member.survey_completed()

    def set_is_resuming_survey(self):
         self.set_attribute_from_session('IS_RESUMING', 'is_resuming_survey')

    def set_has_chosen_retake(self):
        self.set_attribute_from_session('HAS_CHOSEN_RETAKE', 'has_chosen_retake')

    def set_has_answered_retake(self):
        self.set_attribute_from_session('HAS_ANSWERED_RETAKE','has_answered_retake')

    def set_session(self):
        self.session_string = "SESSION-%s-%s" % (self.request['transactionId'], self.__class__.__name__)
        if not cache.get(self.session_string):
            cache.set(self.session_string, self.DEFAULT_SESSION_VARIABLES)

    def clear_caches(self):
        cache.delete(self.session_string)

    def get_from_session(self, key):
        return cache.get(self.session_string)[key]

    def set_in_session(self, key, value):
        session = cache.get(self.session_string)
        session[key] = value
        cache.set(self.session_string, session)

    def set_investigator_cache(self, key, value):
        self.investigator.set_in_cache(key, value)


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

    def get_household_list(self, non_response_reporting=False):
        open_survey = Survey.currently_open_survey(self.investigator.location)
        page = self.get_from_session('PAGE')
        self.responseString += "%s\n%s" % (
            self.MESSAGES['HOUSEHOLD_LIST'],
            self.investigator.households_list(page, registered=False, open_survey=open_survey,
                                              non_response_reporting=non_response_reporting))

    def clean_investigator_input(self):
        if self.is_new_request():
            self.request['ussdRequestString'] = ''

    def select_household(self, answer, non_response_reporting=False):
        try:
            answer = int(answer)
            open_survey = Survey.currently_open_survey(self.investigator.location)
            self.household = self.investigator.all_households(open_survey, non_response_reporting)[answer - 1]
            self.set_in_session('HOUSEHOLD', self.household)
        except (ValueError, IndexError) as e:
            self.responseString += "INVALID SELECTION: "

    def is_invalid_response(self):
        return "INVALID SELECTION: " in self.responseString

    def add_question_prefix(self):
        if self.reanswerable_question():
            self.responseString += "RECONFIRM: "
        if self.invalid_answered_question():
            self.responseString += "INVALID ANSWER: "

    def render_household_members_list(self):
        page = self.get_from_session('PAGE')
        self.responseString += "%s\n%s" % \
                               (self.MESSAGES['MEMBERS_LIST'],
                                self.household.members_list(page, reporting_non_response=True))