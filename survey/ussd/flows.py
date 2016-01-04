'''
    In the cache, paths as follows
    /interviewer/pk/locals  -- current cached variables of on going task (shall mostly be usd
'''
from calendar import monthrange
from django.core import serializers
from survey.models import Interviewer, Interview, Survey, EnumerationArea, \
            Household, HouseholdMember, HouseholdHead, USSDAccess, SurveyAllocation, SurveyHouseholdListing, \
            HouseMemberSurveyCompletion, HouseholdMemberBatchCompletion, HouseholdBatchCompletion, ODKAccess
from django import template
from django.core.cache import cache
from django.conf import settings
from survey.interviewer_configs import LEVEL_OF_EDUCATION, MONTHS, MESSAGES
from collections import OrderedDict
import calendar
from datetime import time, date, datetime
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from dateutil.relativedelta import relativedelta
from utils import *
from django.db.models import Max
#USSD_PREVIOUS, USSD_NEXT, USSD_ITEMS_PER_PAGE

#from django.core.exceptions import ObjectDoesNotExist
DEFAULT_LISTING_SIZE = 1000

class InvalidSelection(ValidationError):
    pass

# def refresh_cache(cls, sender, instance, created, **kwargs):
#     #refresh cache every time some database update happens
#     pass
#
# post_save.connect(refresh_cache, sender=Household)

INVALID_INPUT = 'Invalid Input'
ERROR = 'Error'


class Task(object):
    context = template.Context()

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def survey_listing(self):
        return SurveyHouseholdListing.get_or_create_survey_listing(self.interviewer, self.ongoing_survey)

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def house_listing(self):
        return self.survey_listing.listing

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def survey_allocation(self):
        return SurveyAllocation.get_allocation_details(self.interviewer)

    @survey_allocation.setter
    @saves_to_cache(store=GLOBALS_NP)
    def survey_allocation(self, survey_allocation):
        pass

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def ongoing_survey(self):
        return self.survey_allocation.survey

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def enumeration_area(self):
        return self.survey_allocation.allocation_ea

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def open_batches(self):
        return self.enumeration_area.open_batches(self.ongoing_survey)
        
    @property
    def registered_households(self):
        return self.interviewer.present_households(survey=self.ongoing_survey)

    @property
    @reads_from_cache(store=ONGOING_COMMAND_NP)
    def ongoing_command(self):
        pass

    @ongoing_command.setter
    @refreshes_cache(store=LOCALS_NP)
    @saves_to_cache(store=ONGOING_COMMAND_NP)
    def ongoing_command(self, command):
        pass
    
    @property
    @reads_from_cache(store=GLOBALS_NP)
    def survey_households(self):
        if self.survey_allocation.stage == SurveyAllocation.SURVEY:
            return self.interviewer.survey_households(self.ongoing_survey)
        
    def __init__(self, ussd_access):
        self.access = ussd_access
        interviewer = ussd_access.interviewer
        self.interviewer = interviewer
        if not self.ongoing_command == type(self).__name__:
            print ' is now cleaning up variable space', type(self).__name__
            self.ongoing_command = type(self).__name__

    def intro(self):
        if self.ongoing_survey and self.open_batches:
            return self._intro()
        else:
            return MESSAGES['NO_OPEN_BATCH']
    
    def _intro(self):
        restart_prompt = '%s:Restart'%settings.USSD_RESTART
        intro_speech = self._intro_speech
        if not intro_speech.endswith(restart_prompt):
            intro_speech = '\n'.join([intro_speech, restart_prompt])
        return intro_speech

    def respond(self, message):
        restart_prompt = '%s:Restart'%settings.USSD_RESTART
        response = ''
        if self.ongoing_survey:
            message = message.strip()
            if message == settings.USSD_RESTART:
                access = self.access
                response = Start(access).intro()
            else:
                response = self._respond(message)
        else:
            response = MESSAGES['NO_OPEN_BATCH']
        if not response.endswith(restart_prompt):
            response = '\n'.join([response, restart_prompt])
        return response
    
class Start(Task):
    START_LISTING = 1
    SELECT_HOUSEHOLD = 1
    NEW_HOUSEHOLD = 2
    
    def __init__(self, ussd_access):
        super(Start, self).__init__(ussd_access)
        context = template.Context({'interviewer': self.interviewer.name, 'survey':  self.ongoing_survey})
        self._intro_speech = template.Template(MESSAGES['START']).render(context)
        if self.ongoing_survey.has_sampling and self.survey_allocation.stage in [None, SurveyAllocation.LISTING]:
            self._intro_speech = '\n'.join([self._intro_speech,
                                            '%s: %s'% (self.START_LISTING, MESSAGES['START_LISTING'])])
        else:
            self._intro_speech = '\n'.join([self._intro_speech,
                                            '%s: %s'%(self.SELECT_HOUSEHOLD, MESSAGES['SELECT_HOUSEHOLD'])])
        if self.ongoing_survey.has_sampling is False:
            self._intro_speech = '\n'.join([self._intro_speech,
                                            '%s: %s'%(self.NEW_HOUSEHOLD, MESSAGES['NEW_HOUSEHOLD'])])
            
    def _intro(self):
        return self._intro_speech
        
    def _respond(self, message):
        if message.isdigit():
            if self.ongoing_survey.has_sampling and self.survey_allocation.stage in [None, SurveyAllocation.LISTING]:
                if int(message) == self.START_LISTING:
                    return ListHouseholds(self.access).intro()
            elif int(message) == self.SELECT_HOUSEHOLD:
                return SelectHousehold(self.access).intro()
            elif self.ongoing_survey.has_sampling is False and int(message) == self.NEW_HOUSEHOLD:
                return RegisterHousehold(self.access).intro()
        return self.intro()

class ListHouseholds(Task):
    MALE = 1
    FEMALE = 2
    REGISTER_ANOTHER = 1
    DONT_REGISTER_ANOTHER = 2

    @property
    @reads_from_cache(store=LOCALS_NP)
    def hl_prompts(self):
        return OrderedDict([
            ('physical_address' , 'Enter the physical address'),
            ('head_desc', 'Enter name of head'),
            ('head_sex', '\n'.join(['Enter sex:', '%s. Male'%ListHouseholds.MALE,
                                   '%s. Female'%ListHouseholds.FEMALE])),
            ('register_another', '\n'.join(['Thank you for completing listing for this household. '
                                           'Have you completed listing for %s?' % self.interviewer.ea,
                                           '%s. Yes'%ListHouseholds.DONT_REGISTER_ANOTHER,
                                           '%s. No'%ListHouseholds.REGISTER_ANOTHER]))
        ])

    @refreshes_cache(store=LOCALS_NP)
    def restart_listing(self):
        return self.intro()

    @hl_prompts.setter
    @saves_to_cache(store=LOCALS_NP)
    def hl_prompts(self, prompts):
        pass

    @property
    @reads_from_cache(store=LOCALS_NP)
    def hl_results(self):
        return {}

    @hl_results.setter
    @saves_to_cache(store=LOCALS_NP)
    def hl_results(self, results):
        pass

    @property
    @reads_from_cache(store=LOCALS_NP)
    def next_house(self):
        return Household.objects.filter(listing=self.house_listing)\
                    .aggregate(Max('house_number')).get('house_number__max', 0) + 1

    @next_house.setter
    # @saves_to_cache(store=LOCALS_NP)
    def next_house(self, house_number):
        pass

    def _intro(self):
        return '\n'.join([MESSAGES['HOUSEHOLD_LIST'], 'HH-%s'%self.next_house, self._intro_speech])

    @property
    def _intro_speech(self):
        if len(self.hl_prompts) > 0:
            return self.hl_prompts.values()[0]
        else:
            return Start(self.access).intro()

    def _respond(self, message):
        if self.hl_prompts.keys()[0] in ['head_sex', 'register_another'] and message not in ['1', '2']:
            return self.intro()
        if len(self.hl_prompts) > 0:
            hl_prompts = self.hl_prompts
            prompt = hl_prompts.popitem(0)
            self.hl_prompts = hl_prompts
            results = self.hl_results
            results[prompt[0]] = message
            self.hl_results = results
            if prompt[0] == 'head_sex': #save on last house attribute
                next_house = self.next_house
                Household.objects.create(
                            house_number=next_house,
                             listing=self.house_listing,
                             last_registrar=self.interviewer,
                             registration_channel=USSDAccess.choice_name(),
                             physical_address=self.hl_results['physical_address'],
                             head_desc=self.hl_results['head_desc'],
                             head_sex=self.hl_results['head_sex']
                )
                self.next_house = next_house + 1
            if prompt[0] == 'register_another':
                if message == str(ListHouseholds.REGISTER_ANOTHER):
                    return self.restart_listing()
                else:
                    survey_allocation = self.survey_allocation
                    survey_allocation.stage = SurveyAllocation.SURVEY
                    survey_allocation.save()
                    self.survey_allocation = survey_allocation
                    self.interviewer.generate_survey_households(self.ongoing_survey)
                    return Start(self.access).intro() #back to main menu
            return self.hl_prompts.values()[0]
        else:
            return Start(self.access).intro()

class RegisterHousehold(Task):

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def next_house(self):
        return Household.objects.filter(listing=self.house_listing)\
                    .aggregate(Max('house_number')).get('house_number__max', 0) + 1

    @next_house.setter
    @saves_to_cache(store=GLOBALS_NP)
    def next_house(self, house_number):
        pass

    def _intro(self):
        return '\n'.join([MESSAGES['HOUSE_REGISTRATION'], 'HH-%s'%self.next_house, self._intro_speech])

    @property
    def _intro_speech(self):
        return 'Enter the physical address'

    def _respond(self, message):
        next_house = self.next_house
        household = Household.objects.create(
                            house_number=next_house,
                             listing=self.house_listing,
                             last_registrar=self.interviewer,
                             registration_channel=USSDAccess.choice_name(),
                             physical_address=message
                )
        self.next_house = next_house + 1
        task = RegisterMember(self.access)
        task._household = household
        return task.intro()

class SelectHousehold(Task):

    @property
    def _intro_speech(self):
        lines = self.houselist
        lines.insert(0, MESSAGES['SELECT_HOUSEHOLD'])
        if self.current_page != 0:
            lines.append('%s:Previous' % settings.USSD_NEXT)
        if self.current_page < len(lines)/settings.USSD_ITEMS_PER_PAGE:
            lines.append('%s:Next' % settings.USSD_NEXT)
        return '\n'.join(lines)

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def survey_households(self):
        return self.interviewer.survey_households(self.ongoing_survey)

    @property
    @reads_from_cache(store=GLOBALS_NP)
    def completed_households(self):
        return HouseholdBatchCompletion.objects.filter(batch__in=self.open_batches, interviewer=self.interviewer).\
                                values_list('household', flat=True)

    @completed_households.setter
    @saves_to_cache(store=GLOBALS_NP)
    def completed_households(self, households):
        pass

    @property
    def total_households(self):
        return len(self.survey_households)
    
    @property
    @reads_from_cache(store=LOCALS_NP)
    def current_page(self):
        return 0
    
    @current_page.setter
    @reads_from_cache(store=LOCALS_NP)
    def current_page(self, val):
        if val < 0:
            val = 0
        if val > (self.total_households/settings.USSD_ITEMS_PER_PAGE):
            val = self.total_households/settings.USSD_ITEMS_PER_PAGE + 1
        return val

    @property
    def houselist(self):
        #if list exists in cache fetch, else get from db and put in cache
        total_households = self.total_households
        start_from = self.current_page * settings.USSD_ITEMS_PER_PAGE+1
        start_to = start_from+settings.USSD_ITEMS_PER_PAGE
        if start_to > total_households:
            start_to = total_households+1
        lines = []
        households = self.survey_households[start_from-1:start_to]
        completed_households = self.completed_households
        for h in households:
            if h in completed_households:
                lines.append('%s*'%str(h))
            else:
                lines.append(str(h))
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

    def _respond(self, message):
        selection = self._select(message)
        if selection is not None:
            try:
                household = Household.objects.get(
                                                    listing__ea=self.enumeration_area,
                                                           listing__survey_houselistings__survey=self.ongoing_survey,
                                                           house_number=selection
                                                           )
            except Household.DoesNotExist:
                self._intro_speech = '\n'.join([INVALID_INPUT, self._intro_speech])
                return self.intro()
            ##check if there is an uncompleted interview with this household
            interviews = Interview.objects.filter(interviewer=self.interviewer,
                                                               householdmember__household=household,
                                                               batch__in=self.open_batches,
                                                               closure_date__isnull=True
                                                               )
            if interviews.exists():
                interview = interviews[0]
                task = ConfirmContinue(self.access)
                task._house_member = interview.householdmember
                task._ongoing_interview = interview
            else:
                task = RegisterMember(self.access)
                task._household = household
            return task.intro()
        return self.intro()

class RegisterMember(Task):
    IS_HEAD = 'is_head'
    SURNAME = 'surname'
    FIRSTNAME = 'first_name'
    GENDER = 'gender'
    DOB = 'date_of_birth'
    MALE = 1
    FEMALE = 2

    PROMPTS = OrderedDict([
                    (IS_HEAD, 'Is this the main respondent\n1.Yes\n2.No'),
                   (SURNAME, 'Please enter your surname:\n'),
                   (FIRSTNAME, 'Please enter your first name:\n'),
                   (GENDER, 'Please enter the gender:\n1.Male\n2.Female.' ), #these functions should return intro speech by default
                   (DOB,  'Please Enter Age:')
                   ])

    @property
    @reads_from_cache(store=LOCALS_NP)
    def _household(self):
        pass

    @_household.setter
    @saves_to_cache(store=LOCALS_NP)
    def _household(self, household):
        pass

    @property
    @reads_from_cache(store=LOCALS_NP)
    def house_head(self):
        return self._household.get_head()

    def extractor(self):
        return {
            self.DOB: self._get_dob,
            self.IS_HEAD: self._get_one_or_two,
            self.GENDER: self._get_one_or_two
        }

    @property
    @reads_from_cache(store=LOCALS_NP)
    def pending_prompts(self):
        if self.house_head and self.PROMPTS.has_key(self.IS_HEAD):
            del(self.PROMPTS[self.IS_HEAD])
        prompts = self.PROMPTS.items()
        return OrderedDict(prompts)

    def reset(self):
        self.pending_prompts = None
        return self.pending_prompts

    @pending_prompts.setter
    @saves_to_cache(store=LOCALS_NP)
    def pending_prompts(self, prompts):
        pass

    @property
    @reads_from_cache(store=LOCALS_NP)
    def hm_details(self):
        return {}

    @hm_details.setter
    @saves_to_cache(store=LOCALS_NP)
    def hm_details(self, prompts):
        pass

    def _get_dob(self, message):
        current_val = None
        try:
            current_val = datetime.now() - relativedelta(years=int(message))
        except:
            pass
        return current_val

    def _get_one_or_two(self, message):
        current_val = None
        if message.isdigit() and int(message) in [1, 2]:
            if int(message) == self.MALE:
                current_val = True
            else:
                current_val = False
        return current_val
            
    @property
    def _intro_speech(self):
        pending_prompts = self.pending_prompts
        if len(pending_prompts) > 0:
            return self.pending_prompts.values()[0]

    def _intro(self):
        return '\n'.join([MESSAGES['REGISTER_MEMBER'], self._intro_speech])

    def _respond(self, message):
        pending_prompts = self.pending_prompts
        if pending_prompts:
            attrs = pending_prompts.keys()
            extractor = self.extractor().get(attrs[0], None)
            if extractor and hasattr(extractor, '__call__'):
                attr_val =  extractor(message)
            else:
                attr_val = message
            if attr_val is None:
                return '\n'.join([INVALID_INPUT, self.intro()])
            else:
                hm_details = self.hm_details
                hm_details[attrs[0]] = attr_val
                self.hm_details = hm_details
                pending_prompts.popitem(0) #whatever the case, we've treated this one. Hence pop it
                self.pending_prompts = pending_prompts
                if not pending_prompts: #no more prompts
                    if hm_details.get(self.IS_HEAD):
                        hm = HouseholdHead.objects.create(household=self._household,
                                           surname=hm_details.get(self.SURNAME),
                                           first_name=hm_details.get(self.FIRSTNAME),
                                           date_of_birth=hm_details.get(self.DOB),
                                           gender=hm_details.get(self.GENDER),
                                           survey_listing=self.survey_listing,
                                           registrar=self.interviewer,
                                           registration_channel=USSDAccess.choice_name()
                                           )
                    else:
                        hm = HouseholdMember.objects.create(household=self._household,
                                           surname=hm_details.get(self.SURNAME),
                                           first_name=hm_details.get(self.FIRSTNAME),
                                           date_of_birth=hm_details.get(self.DOB),
                                           gender=hm_details.get(self.GENDER),
                                           survey_listing=self.survey_listing,
                                           registrar=self.interviewer,
                                           registration_channel=USSDAccess.choice_name()
                                           )
                    task = StartInterview(self.access)
                    task._house_member = hm
                    return task.intro()
        else:
            self.reset()
        return self.intro()

class Interviews(Task):
    
    @property
    @reads_from_cache(store=LOCALS_NP)
    def _ongoing_interview(self):
        print 'pending batches is ', self._pending_batches
        if self._pending_batches:
            interview,_ = Interview.objects.get_or_create(interviewer=self.interviewer,
                                                               householdmember=self._house_member,
                                                               batch=self._pending_batches[0],
                                                               interview_channel=self.access,
                                                               closure_date__isnull=True
                                                               )
            return interview
    
    @_ongoing_interview.setter
    @saves_to_cache(store=LOCALS_NP)
    def _ongoing_interview(self, interview):
        pass

    @property
    @reads_from_cache(store=LOCALS_NP)
    def _house_member(self):
        pass

    @_house_member.setter
    @saves_to_cache(store=LOCALS_NP)
    def _house_member(self, hm):
        pass

    @property
    @reads_from_cache(store=LOCALS_NP)
    def _pending_batches(self):
        return Interview.pending_batches(self._house_member, self.enumeration_area,
                                         self.ongoing_survey, self.open_batches)

    @_pending_batches.setter
    @saves_to_cache(store=LOCALS_NP)
    def _pending_batches(self, batches):
        pass
    
    def respond(self, message):
        try:
            return super(Interviews, self).respond(message)
        except:
            return self.intro()

class ConfirmContinue(Interviews):

    RESUME_INTERVIEW = 1
    RESTART_INTERVIEW = 2

    @property
    def _intro_speech(self):
        context = template.Context({'batch': self._ongoing_interview.batch.name,
                                    'house_member':  self._house_member})
        return template.Template(MESSAGES['RESUME_MESSAGE']).render(context)


    def _respond(self, message):
        if message.isdigit():
            selection = int(message)
            if selection in (self.RESTART_INTERVIEW, self.RESUME_INTERVIEW):
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
                task._house_member = house_member
                task._ongoing_interview = interview
                return task.intro()
            else:
                self._intro_speech = '\n'.join([INVALID_INPUT, self._intro_speech])
        else:
            return self.intro()

class StartInterview(Interviews):

    @property
    def _intro_speech(self):
        if self._has_next:
            return self._respond(None)
        else:
            return EndMemberSurvey.get_new(self._house_member, self.access)
    
    @property
    def _has_next(self):
        return len(self._pending_batches) > 0
    
    def _respond(self, message):
        ongoing_interview = self._ongoing_interview
        try:
            response = ongoing_interview.respond(reply=message, channel=USSDAccess.choice_name())
        except:
            response = '\n'.join([ERROR, self.intro()])
        self._ongoing_interview = ongoing_interview #probably something may have happened to the interview instance in db
        if ongoing_interview.is_closed():
            house_member = ongoing_interview.householdmember
            house_member.batch_completed(ongoing_interview.batch)
            batches = self._pending_batches
            batches.pop(0) #pop off the present batch
            self._pending_batches = batches
            if self._pending_batches:
                #start next batch and respond
                interview, created = Interview.objects.get_or_create(interviewer=self.interviewer,
                                                householdmember=house_member,
                                                batch=self._pending_batches[0],
                                                interview_channel=self.access)
                if created:
                    self._ongoing_interview = interview
                    return self.intro()
                else:
                    task = ConfirmContinue(self.access)
                    task._ongoing_interview = interview
                    task._pending_batches = batches
                    return task.intro()
            else:
                return EndMemberSurvey.get_new(house_member, self.access)
        else:
            return response
    
class EndMemberSurvey(Task):
    
    NEXT_MEMBER = 1
    NEW_HOUSE = 2 
    
    def __init__(self, ussd_access):
        super(EndMemberSurvey, self).__init__(ussd_access)
        self._ongoing_interview = None

    @property
    @reads_from_cache(store=LOCALS_NP)
    def _household(self):
        pass

    @_household.setter
    @saves_to_cache(store=LOCALS_NP)
    def _household(self, household):
        pass

    @property
    def _intro_speech(self):
        return MESSAGES['MEMBER_SUCCESS_MESSAGE']
    
    def _respond(self, message):
        selection = int(message)
        if selection == self.NEXT_MEMBER:
            present_household = self._household
            task = RegisterMember(self.access)
            task._household = present_household
            return task.intro()
        else:
            self._household.survey_completed(self.ongoing_survey, self.interviewer)
            task = Start(self.access)
            return task.intro()

    @classmethod
    def get_new(cls, house_member, access):
        house_member.survey_completed()
        task = EndMemberSurvey(access)
        task._household = house_member.household
        return task.intro()

