from calendar import monthrange
import datetime
from django.core import serializers
from survey.models import Interviewer, Survey
from django import template

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
    'HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE': "Count must be greater than %s. How many households have you listed in your Enumeration Area?" % NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER,
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

class Task:
    context = template.Context()
    
    
    def __init__(self, interviewer):
        self.interviewer = interviewer
    
    def intro(self):
        return (self.__class__.__name__, self.intro_speech) 
    
class Start(Task):
    RESGISTER_HOUSEHOLDS = 1
    TAKE_SURVEY = 2
    
    
    def __init__(self, interviewer):
        super(Start, self).__init__(interviewer)
        context = template.Context({'interviewer': interviewer.name})
        self.intro_speech = template.Template(MESSAGES['START']).render(context)
        
    def repond(self, message):
        if int(message.strip()) == RESGISTER_HOUSEHOLDS:
            return RegisterHouseholds(self.interviewer).intro()
        if int(message.strip()) == TAKE_SURVEY:
            return RegisterHouseholds(self.interviewer).intro()
        else:
            return self.intro()
            
        
class RegisterHouseholds(Task):
    pass

class ListHouseholds(Task):
    
    def on_receive(self, message):
        pass

class StartSurvey(Task):
    pass 
