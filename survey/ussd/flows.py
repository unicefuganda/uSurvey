'''
    In the cache, paths as follows
    /interviewer/pk/locals  -- current cached variables of on going task (shall mostly be usd
'''
from calendar import monthrange
from django.core import serializers
from survey.models import Interviewer, Interview, Survey, EnumerationArea, \
            Household, HouseholdMember, HouseholdHead, USSDAccess, SurveyAllocation, \
            HouseMemberSurveyCompletion, HouseholdMemberBatchCompletion, HouseholdBatchCompletion
from django import template
from django.core.cache import cache
from django.conf import settings
from survey.interviewer_configs import LEVEL_OF_EDUCATION, MONTHS, MESSAGES
from collections import OrderedDict
import calendar
from datetime import time, date, datetime
from django.core.exceptions import ValidationError
#USSD_PREVIOUS, USSD_NEXT, USSD_ITEMS_PER_PAGE

#from django.core.exceptions import ObjectDoesNotExist

class InvalidSelection(ValidationError):
    pass


class Task(object):
    context = template.Context()
    
    def _set_global(self, name, val):
        return cache.set('%s/%s' % (self.GLOBALS_SPACE, name), val)
    
    def _retrieve_global(self, name, fallback=None):
        return cache.get('%s/%s' % (self.GLOBALS_SPACE, name), fallback)
    
    @property
    def ongoing_survey(self):
        ongoing = self._retrieve_global('ongoing_survey', None)
        if ongoing is None:
            try:
                ongoing = SurveyAllocation.get_allocation(self.interviewer)
                self._set_global('ongoing_survey', ongoing)
            except SurveyAllocation.DoesNotExist:
                pass
        return ongoing
    
    @property
    def enumeration_area(self):
        ea = self._retrieve_global('enumeration_area', None)
        if ea is None:
            ea = self.interviewer.ea
            self._set_global('enumeration_area', ea)
        return ea
        
    @property
    def registered_households(self):
        return self.interviewer.present_households(survey=self.ongoing_survey)
    
    @property
    def survey_households(self):
        return self.interviewer.generate_survey_households(self.ongoing_survey)
        
    def __init__(self, ussd_access):
        self.access = ussd_access
        interviewer = ussd_access.interviewer
        self.VARIABLE_SPACE = '/interviewer/%s/locals'%interviewer.pk
        self.GLOBALS_SPACE = '/interviewer/%s/globals'%interviewer.pk
        self.EXEC_SPACE = '/interviewer/%s/ongoing'%interviewer.pk
        if not cache.get(self.EXEC_SPACE) == type(self).__name__:
            print cache.get(self.EXEC_SPACE), ' is now cleaning up variable space', type(self).__name__
            cache.delete_pattern('%s*'%self.VARIABLE_SPACE) #refresh local variables space
            cache.set(self.EXEC_SPACE, type(self).__name__) #claim execution space
        self.interviewer = interviewer
    
    def intro(self):
        if self.ongoing_survey:
            return self._intro()
        else:
            return MESSAGES['NO_OPEN_BATCH']
    
    def _intro(self):
        restart_prompt = '%s:Restart'%settings.USSD_RESTART
        intro_speech = self._intro_speech.strip(restart_prompt)
        return '\n'.join([intro_speech, restart_prompt]) 

    def _set(self, name, val):
        return cache.set('%s/%s' % (self.VARIABLE_SPACE, name), val)
    
    def _retrieve(self, name, fallback=None):
        return cache.get('%s/%s' % (self.VARIABLE_SPACE, name), fallback)
    
    def respond(self, message):
        restart_prompt = '%s:Restart'%settings.USSD_RESTART
        response = ''
        if self.ongoing_survey:
            message = message.strip()
            if message == settings.USSD_RESTART:
                response = Start(self.access).intro()
            else:
                response = self._respond(message)
        else:
            response = MESSAGES['NO_OPEN_BATCH']
        response = response.strip(restart_prompt)
        return '\n'.join([response, restart_prompt])     
    
class Start(Task):
    RESGISTER_HOUSEHOLDS = 1
    TAKE_SURVEY = 2
    
    def __init__(self, ussd_access):
        super(Start, self).__init__(ussd_access)
        context = template.Context({'interviewer': self.interviewer.name, 'survey':  self.ongoing_survey})
        self._intro_speech = template.Template(MESSAGES['START']).render(context)
        if self._survey_can_start:
            self._intro_speech = '%s\n%s' % (self._intro_speech, MESSAGES['START_SURVEY'])
            
    @property
    def _survey_can_start(self):
        can_start = self._retrieve("_survey_can_start", None)
        if can_start is None:
            total_ea_households = self.enumeration_area.total_households
            min_percent_reg_houses = self.ongoing_survey.min_percent_reg_houses
            if self.registered_households.count()*100.0/total_ea_households >= min_percent_reg_houses:
                can_start = True
                self._set("_survey_can_start", True)
        return can_start
            
    def _intro(self):
        return self._intro_speech
        
    def _respond(self, message):
        if message.isdigit():
            if int(message) == self.RESGISTER_HOUSEHOLDS:
                return RegisterHousehold(self.access).intro()
            elif self._survey_can_start and int(message.strip()) == self.TAKE_SURVEY:
                return StartSurvey(self.access).intro()
        return self.intro()
        
class SelectHousehold(Task):

    @property
    def _intro_speech(self):
        lines = self.houselist
        lines.insert(0, MESSAGES['HOUSEHOLD_LIST'])
        if self.current_page != 0:
            lines.append('%s:Previous' % settings.USSD_NEXT)
        if self.current_page < len(lines)/settings.USSD_ITEMS_PER_PAGE:
            lines.append('%s:Next' % settings.USSD_NEXT)
        return '\n'.join(lines)
    
    @property
    def total_households(self):
        return self.enumeration_area.total_households
    
    @property
    def current_page(self):
        return self._retrieve('current_page') or 0
    
    @current_page.setter
    def current_page(self, val):
        if val < 0:
            val = 0
        if val > (self.total_households/settings.USSD_ITEMS_PER_PAGE):
            val = self.total_households/settings.USSD_ITEMS_PER_PAGE + 1
        self._set('current_page', int(val))

    @property
    def houselist(self):
        #if list exists in cache fetch, else get from db and put in cache
        total_households = self.total_households
        start_from = self.current_page * settings.USSD_ITEMS_PER_PAGE+1
        start_to = start_from+settings.USSD_ITEMS_PER_PAGE
        if start_to > total_households:
            start_to = total_households+1
        lines = []
        registered = dict([(h.house_number, unicode(h)) for h in self.registered_households])
        for idx in range(start_from, start_to):
            lines.append(registered.get(idx, 'HH-%s' % idx))
        return lines
        
    def _select(self, message):
        selection = None
        message = message.strip()
        if message == settings.USSD_NEXT:
            self.current_page = self.current_page + 1 
        if message == settings.USSD_PREVIOUS:
            self.current_page -= 1
        if message.isdigit():
            selection = int(message)
        if selection is not None and selection <= self.total_households and selection > 0:
            return selection
        return None

            
class RegisterHousehold(SelectHousehold): 
            
    def _respond(self, message):
        selection = self._select(message)
        if selection is not None:
            household, _ = Household.objects.get_or_create(registrar=self.interviewer, 
                                                           ea=self.enumeration_area,
                                                           registration_channel=USSDAccess.choice_name(),
                                                           survey=self.ongoing_survey,
                                                           house_number=selection
                                                           )
            task = MemberOrHead(self.access)
            task._household =  household
            return task.intro()
        return self.intro()

class MemberOrHead(Task):
    SELECT_RESPONDENT = 1
    SELECT_MEMBER = 2
     
    def __init__(self, ussd_access):
        super(MemberOrHead, self).__init__(ussd_access)
        
    @property
    def _household(self):
        return self._retrieve('household')
        
    @_household.setter
    def _household(self, hs):
        self._set('household', hs)
 
    @property
    def _intro_speech(self):
        if self._household.get_head() is None:
            context = template.Context({'household': self._household})
            return template.Template(MESSAGES['SELECT_HEAD_OR_MEMBER']).render(context)
        else:
            household = self._household
            task = RegisterMember(self.access)
            task._household_member = HouseholdMember(household=household)
            return '\n'.join([MESSAGES['HEAD_REGISTERED'], 
                                             #this step automatically transfers execution to register member 
                                             #next on session managemt. Next request from interviewer ends up calling
                                             #RegisterMember.respond
                                             task.intro()
                                            ])
          
    def _respond(self, message):
        message = message.strip()
        if message.isdigit() and int(message) == self.SELECT_RESPONDENT:
            household = self._household
            task = RegisterMember(self.access)
            task._household_member = HouseholdHead(household=household)
            return task.intro()
        if message.isdigit() and int(message) == self.SELECT_MEMBER:
            household = self._household
            task = RegisterMember(self.access)
            task._household_member = HouseholdMember(household=household)
            return task.intro()
        return self.intro()
                
education_level_prompt = ['Please Choose Level of education', ] 
for idx, e_level in enumerate(LEVEL_OF_EDUCATION):
    education_level_prompt.append('%s. %s' % (idx+1, e_level[0]))
month_prompt = ['Please enter month:\n']
month_prompt.extend(['. '.join((str(mo[0]), str(mo[1]))) for mo in MONTHS])
class RegisterMember(Task):
    SURNAME = 'surname'
    FIRSTNAME = 'first_name'
    GENDER = 'gender'
    DOB = 'date_of_birth'
    OCCUPATION = 'occupation'
    LOE = 'level_of_education'
    RESIDENCEDATE = 'resident_since'
    
    @property
    def pending_prompts(self):
        return self._retrieve('pending_prompts', fallback=[]) 
        
    @pending_prompts.setter
    def pending_prompts(self, prompts):
        self._set('pending_prompts', prompts)
    
    def __init__(self, ussd_access):
        super(RegisterMember, self).__init__(ussd_access)
        self.PROMPTS = OrderedDict([
               (self.SURNAME, 'Please enter your surname:\n'),
               (self.FIRSTNAME, 'Please enter your first name:\n'),
               (self.GENDER, self._get_gender ), #these functions should return intro speech by default
               (self.DOB,  self._get_dob),
               (self.OCCUPATION, 'Please enter Occupation:\n',),
               (self.LOE, self._get_loe),
               (self.RESIDENCEDATE, self._get_residency_date),              
               ])
        if len(self.pending_prompts) == 0: #if prompts has finished restart
            self.pending_prompts = self.PROMPTS.keys()
    
    def _get_dob(self, message=None):
        error_prompt = None
        current_val = None
        _get_dob__PROMPTS = OrderedDict([ ('year', 'Please enter year of birth YYYY\n'),
                                    ('month', '\n'.join(month_prompt)),
                                    ('day', 'Please enter day of birth:\n'),
                                    ])
        prompts = self._retrieve('_get_dob().prompts', ['year', 'month', 'day'])
        params = self._retrieve('_get_dob().params', {})
        ongoing_prompt = _get_dob__PROMPTS[prompts[0]]
        if message and len(prompts) > 0:
            error_prompt = 'Invalid input\n%s'%ongoing_prompt
            if prompts[0] == 'year':
                if message.isdigit() and (int(message)>=1900 and int(message)<=date.today().year):
                    params['year'] = int(message)
                    error_prompt = None
                    prompts.pop(0)
            elif prompts[0] == 'month':
                if message.isdigit() and (int(message)>=1 and int(message)<=12):
                    params['month'] = int(message) 
                    error_prompt = None
                    prompts.pop(0)       
            elif prompts[0] == 'day':
                _, max_days = calendar.monthrange(params['year'], params['month'])
                if message.isdigit() and int(message)>=1 and int(message) <= max_days:
                    params['day'] = int(message)
                    error_prompt = None    
                    prompts.pop(0)
                else:
                    error_prompt = 'Invalid input. %s has %s days in %s\n%s'% (
                                                                             dict(MONTHS)[params['month']], 
                                                                             max_days, 
                                                                             params['year'], 
                                                                             ongoing_prompt[0])
           
        self._set('_get_dob().params', params)
        self._set('_get_dob().prompts', prompts)
        if len(prompts) == 0:
            current_val = date(day=params['day'], month=params['month'], year=params['year']) 
        prompt = error_prompt 
        if prompt is None and len(prompts) > 0:
            prompt = _get_dob__PROMPTS[prompts[0]] #return the first prompt 
        return (prompt, current_val)
    
    
    def _get_gender(self, message=None):
        current_val = None
        prompt = 'Please enter the gender:\n1.Male\n2.Female'
        if message: 
            if message.isdigit() and int(message) in [1, 2]:
                prompt, current_val = None, int(message)
            else:
                prompt = 'Invalid input\n%s'%prompt
        return (prompt, current_val)
    
    def _get_loe(self, message=None):
        current_val = None
        prompt = '\n'.join(education_level_prompt)
        if message:
            if message.isdigit() and int(message) in range(1, len(LEVEL_OF_EDUCATION) + 1):
                prompt, current_val = None, LEVEL_OF_EDUCATION[int(message) - 1][0]
            else:
                prompt = 'Invalid input\n%s'%prompt
        return (prompt, current_val)       

    def _get_residency_date(self, message=None):
        error_prompt = None
        current_val = None
        _get_residency_date__PROMPTS = OrderedDict([ ('year', 'Please enter year you started living here (YYYY)\n'),
                                    ('month', '\n'.join(month_prompt)),
                                    ('day', 'Please enter the day:\n'),
                                    ])
        prompts = self._retrieve('_get_residency_date().prompts', ['year', 'month', 'day'])
        params = self._retrieve('_get_residency_date().params', {})
        ongoing_prompt = _get_residency_date__PROMPTS[prompts[0]]
        if message and len(prompts) > 0:
            error_prompt = 'Invalid input\n%s'%ongoing_prompt
            if prompts[0] == 'year':
                if message.isdigit() and (int(message)>=1900 and int(message)<=date.today().year):
                    params['year'] = int(message)
                    error_prompt = None
                    prompts.pop(0)
            elif prompts[0] == 'month':
                if message.isdigit() and (int(message)>=1 and int(message)<=12):
                    params['month'] = int(message) 
                    error_prompt = None
                    prompts.pop(0)       
            elif prompts[0] == 'day':
                _, max_days = calendar.monthrange(params['year'], params['month'])
                if message.isdigit() and int(message)>=1 and int(message) <= max_days:
                    params['day'] = int(message)
                    error_prompt = None    
                    prompts.pop(0)
                else:
                    error_prompt = 'Invalid input. %s has %s days in %s\n%s'% (
                                                                             dict(MONTHS)[params['month']], 
                                                                             max_days, 
                                                                             params['year'], 
                                                                             ongoing_prompt[0])
            
            self._set('_get_residency_date().params', params)
            self._set('_get_residency_date().prompts', prompts)
            if len(prompts) == 0:
                current_val = date(day=params['day'], month=params['month'], year=params['year']) 
        prompt = error_prompt 
        if prompt is None and len(prompts) > 0:
            prompt = _get_residency_date__PROMPTS[prompts[0]] #return the first prompt 
        return (prompt, current_val)

    
    @property
    def _household_member(self):
        return self._retrieve('household_member')
        
    @_household_member.setter
    def _household_member(self, member):
        self._set('household_member', member)        
            
    @property
    def _intro_speech(self):
        pending_prompts = self.pending_prompts
        if len(pending_prompts) > 0:
            prompt_desc = self.PROMPTS[pending_prompts[0]]
            if hasattr(self._household_member, pending_prompts[0]): #if prompt is applicable
                if hasattr(prompt_desc, '__call__'):
                    return prompt_desc()[0] #callable prompt handlers return tuple (prompt text, current value)
                else:
                    return prompt_desc
            else:
                pending_prompts.pop(0) #remove irrelevant
                self.pending_prompts = pending_prompts #becaus the pending prompts are cached
                return self._intro_speech
        else:
            return self.end_registration()
    
    def _respond(self, message):
        pending_prompts = self.pending_prompts
        if pending_prompts:
            household_member = self._household_member
            prompt_desc = self.PROMPTS[pending_prompts[0]]
            if hasattr(household_member, pending_prompts[0]):
                if hasattr(prompt_desc, '__call__'):
                    next_prompt, attr_val =  prompt_desc(message)
                    if next_prompt:
                        return next_prompt
                else:
                    attr_val = message
                setattr(household_member, pending_prompts[0], attr_val)
            pending_prompts.pop(0) #whatever the case, we've treated this one. Hence pop it
            self.pending_prompts = pending_prompts
            self._household_member = household_member
        return self.intro()
    
    def end_registration(self):
        household_member = self._household_member
        household_member.save()
        task = EndRegistration(self.access) 
        task._household = household_member.household
        return task.intro()
        
class EndRegistration(Task):
    REGISTER_NEW = 1
    DONT_REGISTER_NEW = 2
    def __init__(self, ussd_access):
        super(EndRegistration, self).__init__(ussd_access)
    
    @property
    def _household(self):
        return self._retrieve('household')
        
    @_household.setter
    def _household(self, hs):
        self._set('household', hs)      
    
    @property
    def _intro_speech(self):
        return MESSAGES['END_REGISTRATION']
    
    def _respond(self, message):
        message = message.strip()
        if message.isdigit():
            if int(message) == self.REGISTER_NEW: 
                household = self._household
                task = MemberOrHead(self.access)
                task._household =  household
                return task.intro()
            if int(message) == self.DONT_REGISTER_NEW: 
                return Start(self.access).intro()
        return self.intro()        


class Interviews(Task):
    
    def __init__(self, ussd_access):
        super(Interviews, self).__init__(ussd_access)
        self.INVERVIEW_SPACE = '/interviewer/%s/interviews'%self.interviewer.pk
        
    def _set_param(self, name, val):
        cache.set('%s/%s' % (self.INVERVIEW_SPACE, name), val)
    
    def _get_param(self, name, fallback=None):
        return cache.get('%s/%s' % (self.INVERVIEW_SPACE, name), fallback)
    
    @property
    def _ongoing_interview(self):
        return self._get_param('ongoing_interview')
    
    @_ongoing_interview.setter
    def _ongoing_interview(self, interview):
        self._set_param('ongoing_interview', interview)
    
    @property    
    def _pending_batches(self):
        return self._get_param('pending_batches')
    
    @_pending_batches.setter
    def _pending_batches(self, batches):
        return self._set_param('pending_batches', batches)       
    
    def respond(self, message):
        try:
            return super(Interviews, self).respond(message)
        except:
            return StartSurvey(self.access).respond(message)
    
    
class StartSurvey(SelectHousehold):
    
    @property
    def house_roaster(self):
        registered = self._retrieve('house_register', None)
        if registered is None:
            registered = dict([(int(h.house_number), unicode(h)) for h in self.registered_households if h.members.count()>0])
            self._set('house_register', registered)
        return registered
    
    @property
    def houselist(self):
        #if list exists in cache fetch, else get from db and put in cache
        total_households = len(self.house_roaster.keys())
        start_from = self.current_page * settings.USSD_ITEMS_PER_PAGE+1
        start_to = start_from+settings.USSD_ITEMS_PER_PAGE
        if start_to > total_households:
            start_to = total_households+1
        lines = []
        registered = self.house_roaster
        for idx in registered.keys():
            lines.append(registered.get(idx))
        return lines
    
    def _select(self, message):
        selection = None
        message = message.strip()
        if message == settings.USSD_NEXT:
            self.current_page = self.current_page + 1 
        if message == settings.USSD_PREVIOUS:
            self.current_page -= 1
        if message.isdigit():
            selection = int(message)
        registered = self.house_roaster
        if selection in registered.keys():
            return selection
        return None
            
    def _respond(self, message):
        selection = self._select(message)
        if selection is None:
            return self.intro()
        else:
            household = Household.objects.get(registrar=self.interviewer,
                                                           ea=self.enumeration_area,
                                                           registration_channel=USSDAccess.choice_name(),
                                                           survey=self.ongoing_survey,
                                                           house_number=selection
                                                           )
            task = SelectMember(self.access)
            task._household =  household
            return task.intro()
        
class SelectMember(Interviews):

    def __init__(self, ussd_access):
        super(SelectMember, self).__init__(ussd_access)
    
    @property
    def _household(self):
        return self._retrieve('household')
        
    @_household.setter
    def _household(self, hs):
        self._set('household', hs)

    @property
    def _intro_speech(self):
        lines = self._memberlist
        lines.insert(0, MESSAGES['MEMBERS_LIST'])
        if self.current_page != 0:
            lines.append('%s:Previous' % settings.USSD_NEXT)
        if self.current_page < len(lines)/settings.USSD_ITEMS_PER_PAGE:
            lines.append('%s:Next' % settings.USSD_NEXT)
        return '\n'.join(lines)
    
    @property
    def _total_members(self):
        return self._house_members.count()
    
    @property
    def registered_households(self):
        return self.interviewer.present_households()
    
    @property
    def current_page(self):
        return self._retrieve('current_page') or 0
    
    @current_page.setter
    def current_page(self, val):
        if val < 0:
            val = 0
        if val > (self._total_members/settings.USSD_ITEMS_PER_PAGE):
            val = self._total_members/settings.USSD_ITEMS_PER_PAGE + 1
        self._set('current_page', int(val))
        
    @property
    def _house_members(self):
        members = self._retrieve("house_members", None)
        if members is None:
            completion_records = HouseMemberSurveyCompletion.objects.filter(householdmember__household=self._household, 
                                                       interviewer=self.interviewer,
                                                       survey=self.ongoing_survey)
            members = self._household.members.exclude(pk__in=[c_r.householdmember.pk 
                                                              for c_r in completion_records]).order_by('first_name')
            self._set('house_members', members) #better to cache this list to prevent changes before response from affecting
        return members
        
    @property
    def _memberlist(self):
        memberlist = self._house_members
        total_members = self._total_members
        start_from = self.current_page * settings.USSD_ITEMS_PER_PAGE+1
        start_to = start_from+settings.USSD_ITEMS_PER_PAGE
        if start_to > total_members:
            start_to = total_members+1
        lines = []
        for idx in range(start_from, start_to):
            lines.append( '%s. %s\n'% (idx, memberlist[idx-1]))
        return lines
        
    def _select(self, message):
        selection = None
        message = message.strip()
        if message == settings.USSD_NEXT:
            self.current_page = self.current_page + 1 
        if message == settings.USSD_PREVIOUS:
            self.current_page -= 1
        if message.isdigit():
            selection = int(message)
        if selection is not None and selection <= len(self._memberlist) and selection > 0:
            return selection
        return None

    def _respond(self, message):
        selection = self._select(message)
        if selection is None:
            return self.intro()
        else:
            selection = int(selection)
            house_member = self._house_members[selection-1]
#             task._house_member = self._memberlist[selection]
            pending_batches = Interview.pending_batches(house_member, self.enumeration_area, self.ongoing_survey)
            if len(pending_batches):
                interview, created = Interview.objects.get_or_create(interviewer=self.interviewer, 
                                                householdmember=house_member,
                                                batch=pending_batches[0],
                                                interview_channel=self.access)
                if created:
                    task = StartInterview(self.access)
                else:
                    task = ConfirmContinue(self.access)
                task._ongoing_interview = interview
                task._pending_batches = pending_batches[1:]
                return task.intro()
            else:
                return MESSAGES['NO_OPEN_BATCH'] 

class ConfirmContinue(Interviews):
    
    RESUME_INTERVIEW = 1
    RESTART_INTERVIEW = 2
    
    @property
    def _intro_speech(self):
        return MESSAGES['RESUME_MESSAGE']
        
    
    def _respond(self, message):
        if message.isdigit():
            selection = int(message)
            if selection in (self.RESTART_INTERVIEW, self.RESUME_INTERVIEW):
                open_batches = self._pending_batches
                interview = self._ongoing_interview
                house_member = self._ongoing_interview.householdmember
                if selection == self.RESTART_INTERVIEW:
                    self._ongoing_interview.delete()
                    interview = Interview.objects.create(interviewer=self.interviewer, 
                                                    householdmember=house_member,
                                                    batch=self._ongoing_interview.batch,
                                                    interview_channel=self.access)
                    self._ongoing_interview = interview
                task = StartInterview(self.access)
                # task._ongoing_interview = interview
#                 task._pending_batches = open_batches
                return task.intro()
        else:
            return self.intro()
                
class StartInterview(Interviews):
    
    def __init__(self, ussd_access):
        super(StartInterview, self).__init__(ussd_access)
        
    @property
    def _intro_speech(self):
        ongoing_interview = self._ongoing_interview
        speech = ongoing_interview.respond(channel=USSDAccess.choice_name())
        self._ongoing_interview = ongoing_interview
        return speech
    
    @property
    def _has_next(self):
        return len(self._pending_batches) > 0
    
    def _respond(self, message):
        if message:
            ongoing_interview = self._ongoing_interview
            response = ongoing_interview.respond(message, channel=USSDAccess.choice_name())
            self._ongoing_interview = ongoing_interview #probably something may have happened to the interview instance in db
            if response is None:
                self._ongoing_interview.closure_date = datetime.now()
                self._ongoing_interview.save()
                house_member = self._ongoing_interview.householdmember
                house_member.batch_completed(ongoing_interview.batch)
                if house_member.household.has_completed_batch():
                    house_member.household.batch_completed(ongoing_interview.batch)
                if self._has_next:
                    batches = self._pending_batches
                    present_batch = batches.pop(0)
                    self._pending_batches = batches
                    #start next batch and respond
                    interview, created = Interview.objects.get_or_create(interviewer=self.interviewer, 
                                                    householdmember=house_member,
                                                    batch=present_batch)
                    if created:
                        self._ongoing_interview = interview
                    else:
                        task = ConfirmContinue(self.access)
                        task._ongoing_interview = interview
                        task._pending_batches = batches
                        return task.intro()
                else:
                    house_member.survey_completed()
                    if house_member.household.has_completed():
                        house_member.household.survey_completed()
                    task = EndMemberSurvey(self.access)
                    task._household = house_member.household
                    task.intro()
            else:
                return response
        return self.intro()    
    
class EndMemberSurvey(Interviews):
    
    NEXT_MEMBER = 1
    NEW_HOUSE = 2 
    
    def __init__(self, ussd_access):
        super(EndMemberSurvey, self).__init__(ussd_access)
        self._ongoing_interview = None
        
        
    @property
    def _household(self):
        self._retrieve("household")
        
    @_household.setter
    def _household(self, hs):
        self._set("_household", hs)
        
    @property
    def _intro_speech(self):
        return MESSAGES['MEMBER_SUCCESS_MESSAGE']
    
    def _respond(self, message):
        selection = int(message)
        if selection == self.NEXT_MEMBER:
            present_household = self._household
            task = SelectMember(self.access)
            task._household = present_household
            return task.intro()
        else:
            task = StartSurvey(self.access)
            return task.intro() 
            
