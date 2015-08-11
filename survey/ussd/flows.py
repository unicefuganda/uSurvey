'''
    In the cache, paths as follows
    /interviewer/pk/locals  -- current cached variables of on going task (shall mostly be usd
'''
from calendar import monthrange
import datetime
from django.core import serializers
from survey.models import Interviewer, Survey, EnumerationArea, \
            Household, HouseholdMember, HouseholdHead, USSDAccess, SurveyAllocation
from django import template
from django.core.cache import cache
from django.conf import settings
from interviewer_configs import LEVEL_OF_EDUCATION, MONTHS 
from collections import OrderedDict
import calendar
from datetime import time
#USSD_PREVIOUS, USSD_NEXT, USSD_ITEMS_PER_PAGE

#from django.core.exceptions import ObjectDoesNotExist

MESSAGES = {
    'UNKNOWN_RESPONSE' : "Pls enter a valid reply",
    'SUCCESS_MESSAGE': "This survey has come to an end. Your responses have been received. Thank you.",
    'BATCH_5_MIN_TIMEDOUT_MESSAGE': "This batch is already completed and 5 minutes have passed. You may no longer retake it.",
    'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for any surveys.",
    'START': "Welcome {{interviewer}} to the survey.\n1: Register households\n2: Take survey",
    'HOUSEHOLD_LIST': "Please enter household from the list or enter the sequence number",
    'MEMBERS_LIST': "Please select a member from the list",
    'SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS': "Survey Completed. Thank you.",
    'RETAKE_SURVEY': "You have already completed this household. Would you like to start again?\n1: Yes\n2: No",
    'NO_HOUSEHOLDS': "Sorry, you have no households registered.",
    'NO_OPEN_BATCH': "Sorry, currently there are no open surveys.",
    'HOUSEHOLDS_COUNT_QUESTION': "How many households have you listed in your Enumeration Area?",
    'HOUSEHOLD_SELECTION_SMS_MESSAGE': "Thank you. You will receive the household numbers selected for your Enumeration Area",
    'HOUSEHOLD_CONFIRMATION_MESSAGE': "Thank you. Houselist for Enumeration Area is available for member registration.",
    'HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE': "Count must be greater than %s. How many households have you listed in your Enumeration Area?", #% NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER,
    'MEMBER_SUCCESS_MESSAGE': "Thank you. Would you like to proceed to the next Household Member?\n1: Yes\n2: No",
    'HOUSEHOLD_COMPLETION_MESSAGE': "Thank you. You have completed this household. Would you like to retake this household?\n1: Yes\n2: No",
    'RESUME_MESSAGE': "Would you like to to resume with member question?\n1: Yes\n2: No",
    'SELECT_HEAD_OR_MEMBER': 'Household %s, please select household member to register:\n1: Respondent\n2: Member',
    'END_REGISTRATION': 'Thank you for registering household member. Would you like to register another member?\n1: Yes\n2: No',
    'INTERVIEWER_BLOCKED_MESSAGE': 'Sorry. You are not registered for any surveys.',
    'HEAD_REGISTERED': "Head already registered for this household. Registering members now:\n",
    'NON_RESPONSE_MENU': "\n3: Report non-response",
    'NON_RESPONSE_COMPLETION': "Thank you. You have completed reporting non-responses. Would you like to start again?\n1: Yes\n2: No",
}



class Task(object):
    context = template.Context()
#     VARIABLE_SPACE = '/interviewer/%s/locals'
#     EXEC_SPACE = '/interviewer/%s/ongoing'
    
    def __init__(self, interviewer):
        self.VARIABLE_SPACE = '/interviewer/%s/locals'%interviewer.pk
        self.EXEC_SPACE = '/interviewer/%s/ongoing'%interviewer.pk
        if not cache.get(self.EXEC_SPACE) == type(self).__name__:
            print cache.get(self.EXEC_SPACE), ' is not cleaning up variable space', type(self).__name__
            cache.delete_pattern('%s*'%self.VARIABLE_SPACE) #refresh local variables space
            cache.set(self.EXEC_SPACE, type(self).__name__) #claim execution space
        self.interviewer = interviewer
    
    def intro(self):
        return '\n'.join([self._intro_speech, '%s:Restart'%settings.USSD_RESTART]) 

    def set(self, name, val):
        return cache.set('%s/%s' % (self.VARIABLE_SPACE, name), val)
    
    def retrieve(self, name):
        return cache.get('%s/%s' % (self.VARIABLE_SPACE, name))
        
    
class NavTask(Task):
    
    def get_next(self):
        pass
    
    def get_prev(self):
        pass
    
    def current(self):
        pass
    
class Start(Task):
    RESGISTER_HOUSEHOLDS = 1
    TAKE_SURVEY = 2
    
    def __init__(self, interviewer):
        super(Start, self).__init__(interviewer)
        context = template.Context({'interviewer': interviewer.name})
        self._intro_speech = template.Template(MESSAGES['START']).render(context)
        
    def intro(self):
        return self._intro_speech
        
    def respond(self, message):
        if int(message.strip()) == self.RESGISTER_HOUSEHOLDS:
            return RegisterHousehold(self.interviewer).intro()
        if int(message.strip()) == self.TAKE_SURVEY:
            return StartSurvey(self.interviewer).intro()
        else:
            return self.intro()
            
class RegisterHousehold(Task): 
    
    _total_households = 0
    
    @property
    def total_households(self):
        self._total_households = self.interviewer.ea.total_households
        return self._total_households
    
    @property
    def already_registered(self):
        return self.interviewer.present_households()
    
    @property
    def current_page(self):
        return self.retrieve('current_page') or 0
    
    @current_page.setter
    def current_page(self, val):
        if val < 0:
            val = 0
        if val > (self.total_households/settings.USSD_ITEMS_PER_PAGE):
            val = self.total_households/settings.USSD_ITEMS_PER_PAGE + 1
        self.set('current_page', int(val))

    @property
    def houselist(self):
        #if list exists in cache fetch, else get from db and put in cache
        total_households = self.total_households
        start_from = self.current_page * settings.USSD_ITEMS_PER_PAGE+1
        start_to = start_from+settings.USSD_ITEMS_PER_PAGE
        if start_to > total_households:
            start_to = total_households+1
        lines = []
        registered = dict([(h.house_number, h) for h in already_registered])
        for idx in range(start_from, start_to):
            lines.append(registered.get(idx, 'HH-%s' % idx))
        return lines
    
    @property
    def _intro_speech(self):
        lines = self.houselist
        lines.insert(0, MESSAGES['HOUSEHOLD_LIST'])
        if self.current_page != 0:
            lines.append('%s:Previous' % settings.USSD_NEXT)
        if self.current_page < len(lines)/settings.USSD_ITEMS_PER_PAGE:
            lines.append('%s:Next' % settings.USSD_NEXT)
        return '\n'.join(lines)
    
    def respond(self, message):
        message = message.strip()
        if message == settings.USSD_NEXT:
            self.current_page = self.current_page + 1 
        if message == settings.USSD_PREVIOUS:
            self.current_page -= 1
        if message.isdigit():
            selection = int(message)
        if selection <= self.total_households and selection > 0:
            household, _ = Household.objects.get_or_set(registrar=self.interviewer, 
                                                           ea=self.interviewer.ea,
                                                           registration_channel=USSDAccess.choice_name(),
                                                           survey=SurveyAllocation.get_allocation(self.interviewer),
                                                           house_number=selection
                                                           )
            return MemberOrHead(self.interviewer, household).intro()
        return self.intro()

class MemberOrHead(Task):
    SELECT_RESPONDENT = 1
    SELECT_MEMBER = 2
     
    def __init__(self, interviewer, household):
        super(RegisterMember, self).__init__(interviewer)
        self._household = household

    @property
    def _household(self):
        return self.retrieve('household')
        
    @_household.setter
    def _household(self, hs):
        self.set('household', hs)
 
    @property
    def _intro_speech(self):
        if self._household.head is None:
            self._intro_speech = MESSAGES['SELECT_HEAD_OR_MEMBER']
        else:
            self._intro_speech = '\n'.join([MESSAGES['HEAD_REGISTERED'], 
                                             #this step automatically transfers execution to register member 
                                             #next on session managemt. Next request from interviewer ends up calling
                                             #RegisterMember.respond
                                            RegisterMember(self.interviewer, self._household).intro()])
          
    def respond(self, message):
        message = message.strip()
        if message.isdigit() and int(message) == self.SELECT_RESPONDENT:
            return RegisterMember(self.interviewer, self._household, as_head=True).intro()
        if message.isdigit() and int(message) == self.SELECT_MEMBER:
            return RegisterMember(self.interviewer, self._household).intro()
        return self.intro()
                
education_level_prompt = ['Please Choose Level of education', ] 
for idx, e_level in enumerate(LEVEL_OF_EDUCATION):
    education_level_prompt.append('%s. %s' % (idx+1, e_level[0]))
month_prompt = ['Please enter month:\n']
month_prompt.extend(['. '.join(mo) for mo in MONTHS])
class RegisterMember(Task):
    SURNAME = 'surname'
    FIRSTNAME = 'first_name'
    GENDER = 'gender'
    DOB = 'date_of_birth'
    OCCUPATION = 'occupation'
    LOE = 'level_of_education'
    RESIDENCEDATE = 'resident_since'
    PROMPTS = OrderedDict([
               (self.SURNAME, 'Please enter your surname:\n'),
               (self.FIRSTNAME, 'Please enter your first name:\n'),
               (self.GENDER, self._get_gender ), #these functions should return intro speech by default
               (self.DOB,  self._get_dob),
               (self.OCCUPATION, 'Please enter Occupation:\n',),
               (self.LOE, self._get_loe),
               (self.RESIDENCEDATE, self._get_residency_date),              
               ])
    
    @property
    def next_prompts(self):
        return self.retrieve('pending_prompts') or OrderedDict()
    
    @next_prompts.setter
    def next_prompts(self, prompts):
        self.set(name, prompts)
    
    def __init__(self, interviewer, household, as_head=False):
        super(RegisterMember, self).__init__(interviewer)
        if as_head:
            self._household_member = HouseholdHead(household=household)
        else:
            self._household_member = HouseholdMember(household=household)
    
    def _get_dob(self, message=None):
        error_prompt = None
        current_val = None
        if message is None:
            prompts = OrderedDict([ ('year', 'Please enter year of birth YYYY\n'),
                                    ('month', '\n'.join(month_prompt)),
                                    ('day', 'Please enter day of birth:\n'),
                                    ])
        else:
            prompts = self.retrieve('_get_dob().prompts')
            if len(prompts) > 0:
                ongoing_prompt = prompts.items[0]
                error_prompt = 'Invalid input\n%s'%ongoing_prompt[0]
                params = self.retrieve('_get_dob().params') or {}
                if ongoing_prompt[0] == 'year':
                    if message.isdigit() and (int(message)>=1900 and int(message)<=date.today().year):
                        params['year'] = int(message)
                        prompts.popitem(False)
                if ongoing_prompt[0] == 'month':
                    if message.isdigit() and (int(message)>=1 and int(message)<=12):
                        params['month'] = int(message) 
                        prompts.popitem(False)       
                if ongoing_prompt[0] == 'day':
                    if message.isdigit() and int(message)>=1:
                        _, max_days = calendar.monthrange(params['year'], params['month'])
                        if int(message)<=max_days:
                            params['day'] = int(message)    
                            prompts.popitem(False)
                        else:
                            error_prompt = 'Invalid input. %s has %s days in %s\n%s'% (
                                                                                 dict(MONTHS)[params['month']], 
                                                                                 params['day'], 
                                                                                 params['year'], 
                                                                                 ongoing_prompt[0])
                   
                self.set('_get_dob().params', params)
                self.set('_get_dob().prompts', prompts)
                if set(params.keys()).issuperset(['day', 'month', 'year']):
                    current_val = date(day=params['day'], month=params['month'], year=params['year']) 
        prompt = error_prompt 
        if prompt is None and len(prompts.items()) > 0:
            prompt =  prompts.items()[0][1] #return the first prompt 
        return (prompt, current_val)
    
    def _get_gender(self, message=None):
        current_val = None
        prompt = 'Please enter the gender:\n1.Male\n2.Female'
        if message is not None:
            if message.isdigit() and int(message) in [1, 2]:
                current_val = int(message)
            else:
                prompt = 'Invalid input\n%s'%prompt
        return (prompt, current_val)
    
    def _get_loe(self, message=None):
        current_val = None
        prompt = '\n'.join(education_level_prompt)
        if message is not None:
            if int(message) < len(LEVEL_OF_EDUCATION) and int(message) > 0:
                current_val = LEVEL_OF_EDUCATION[int(message) - 1][0]
            else:
                prompt = 'Invalid input\n%s'%prompt
        return (prompt, current_val)       

    def _get_residency_date(self, message=None):
        error_prompt = None
        current_val = None
        if message is None:
            prompts = OrderedDict([ ('year', 'Please enter year of residence YYYY\n'),
                                    ('month', '\n'.join(month_prompt)),
                                    ('day', 'Please enter day of residence:\n'),
                                    ])
        else:
            prompts = self.retrieve('_get_residency_date().prompts')
            if len(prompts) > 0:
                ongoing_prompt = prompts.items[0]
                error_prompt = 'Invalid input\n%s'%ongoing_prompt[0]
                params = self.retrieve('_get_residency_date().params') or {}
                if ongoing_prompt[0] == 'year':
                    if message.isdigit() and (int(message)>=1900 and int(message)<=date.today().year):
                        params['year'] = int(message)
                        prompts.popitem(False)
                if ongoing_prompt[0] == 'month':
                    if message.isdigit() and (int(message)>=1 and int(message)<=12):
                        params['month'] = int(message) 
                        prompts.popitem(False)       
                if ongoing_prompt[0] == 'day':
                    if message.isdigit() and int(message)>=1:
                        _, max_days = calendar.monthrange(params['year'], params['month'])
                        if int(message)<=max_days:
                            params['day'] = int(message)    
                            prompts.popitem(False)
                        else:
                            error_prompt = 'Invalid input. %s has %s days in %s\n%s'% (
                                                                                 dict(MONTHS)[params['month']], 
                                                                                 params['day'], 
                                                                                 params['year'], 
                                                                                 ongoing_prompt[0])
                   
                self.set('_get_residency_date().params', params)
                self.set('_get_residency_date().prompts', prompts)
                if set(params.keys()).issuperset(['day', 'month', 'year']):
                    current_val = date(day=params['day'], month=params['month'], year=params['year']) 
        prompt = error_prompt 
        if prompt is None and len(prompts.items()) > 0:
            prompt =  prompts.items()[0][1] #return the first prompt 
        return (prompt, current_val)

    
    @property
    def _household_member(self):
        return self.retrieve('household_member')
        
    @_member_attrs.setter
    def _household_member(self, member):
        self.set('household_member', member)        
            
    @property
    def _intro_speech(self):
        if len(self.next_prompts.items) > 0:
            prompt_desc = self.next_prompts.items[0]
            if hasattr(self._household_member, prompt_desc[0]): #if prompt is applicable
                if hasattr(prompt_desc[1], '__call__'):
                    return prompt_desc[1]()[0] #callable prompt handlers return tuple (prompt text, current value)
                else:
                    return prompt_desc[1]
            else:
                self.next_prompts.pop(prompt_desc[0])
                return self._intro_speech()
                    
    def respond(self, message):
        if self.next_prompts:
            household_member = self._household_member
            prompt_desc = self.next_prompts.items()[0]
            if hasattr(household_member, prompt_desc[0]):
                if hasattr(prompt_desc[1], '__call__'):
                    next_prompt, attr_val =  prompt_desc[1](message)
                    if next_prompt is not None:
                        return next_prompt
                else:
                    attr_val = message
                setattr(household_member, prompt_desc[0], attr_val)
            self.next_prompts.popitem(False)
            next_prompt = self.intro()
            self._household_member = household_member
            if next_prompt is None:
                self._household_member.save()
                return EndRegistration().intro()   
            else:
                return next_prompt 
        return self.intro()
        
class EndRegistration(Task):
    REGISTER_NEW = 1
    DONT_REGISTER_NEW = 2
    def __init__(self, interviewer, household):
        super(EndRegistration, self).__init__(interviewer)
        self._household = household
    
    @property
    def _household(self):
        return self.retrieve('household')
        
    @_household.setter
    def _household(self, hs):
        self.set('household', hs)      
    
    def _intro_speech(self):
        return MESSAGES['END_REGISTRATION']
    
    def respond(self, message):
        message = message.strip()
        if message.isdigit():
            if int(message) == self.REGISTER_NEW: 
                return MemberOrHead(self.interviewer, self._household).intro()
            if int(message) == self.DONT_REGISTER_NEW: 
                return Start(self.interviewer).intro()
        return self.intro()
        
    
class HouseholdSelection(Task):
    _total_households = 0    
    
    def __init__(self, interviewer):
        super(HouseholdSelection, self).__init__(interviewer)
    
    @property
    def total_households(self):
        self._total_households = self.interviewer.ea.total_households
        return self._total_households
    
    @property
    def already_registered(self):
        return self.interviewer.present_households()
    
    @property
    def current_page(self):
        return self.retrieve('current_page') or 0
    
    @current_page.setter
    def current_page(self, val):
        if val < 0:
            val = 0
        if val > (self.total_households/settings.USSD_ITEMS_PER_PAGE):
            val = self.total_households/settings.USSD_ITEMS_PER_PAGE + 1
        self.set('current_page', int(val))

    @property
    def houselist(self):
        #if list exists in cache fetch, else get from db and put in cache
        total_households = self.total_households
        start_from = self.current_page * settings.USSD_ITEMS_PER_PAGE+1
        start_to = start_from+settings.USSD_ITEMS_PER_PAGE
        if start_to > total_households:
            start_to = total_households+1
        lines = []
        registered = dict([(h.house_number, h) for h in already_registered])
        for idx in range(start_from, start_to):
            lines.append(registered.get(idx, 'HH-%s' % idx))
        return lines         

class StartSurvey(Task):
    pass
