#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
import phonenumbers
from django.conf import settings
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from survey.models import SurveyAllocation
from survey.forms.answer import (UserAccessForm, SurveyAllocationForm, SelectBatchForm, AddMoreLoopForm)
from .online_handler import OnlineHandler, show_only_answer_form, get_display_format


def ussd_flow(request):
    request_data = request.GET if request.method == 'GET' else request.POST
    request_data = request_data.copy()
    request_data['format'] = 'text'
    mobile = request_data.get(settings.USSD_MOBILE_NUMBER_FIELD, '')
    try:
        pn = phonenumbers.parse(mobile, settings.COUNTRY_CODE)
        if phonenumbers.is_valid_number_for_region(pn, settings.COUNTRY_CODE):
            mobile = pn.national_number
            request_data['uid'] = mobile
            request_data['value'] = request_data.get(settings.USSD_MSG_FIELD, '')
            if request.method == 'GET':
                request.GET = request_data
            if request.method == 'POST':
                request.POST = request_data
            _response = respond(request)
            response = settings.USSD_RESPONSE_FORMAT % {'response': _response.content.strip()}
        else:
            response = 'Invalid mobile number for your region'
    except phonenumbers.NumberParseException:
        response = 'Invalid mobile number'
    return HttpResponse(response, content_type='text/plain')


def respond(request):
    request_data = request.GET if request.method == 'GET' else request.POST
    if 'uid' in request_data:
        access_form = UserAccessForm(data=request_data)
        if access_form.is_valid():
            access = access_form.cleaned_data['uid']
            handler = OnlineInterview(access, action_url=reverse('online_interviewer_view'))
            return handler.handle_session(request)
    else:
        access_form = UserAccessForm()
    template_file = "interviews/answer.html"
    context = {'button_label': 'send', 'answer_form': access_form,
               'template_file': template_file,
               'id': 'interview_form',
               }
    if show_only_answer_form(request):
        context['display_format'] = get_display_format(request)
        return render(request, template_file, context)
    return render(request, 'interviews/new.html', context)


class OnlineInterview(OnlineHandler):

    def respond(self, request, session_data):
        access = self.access
        # check if there is any active interview, if yes, ask interview last question
        interview = session_data.get('interview', None)
        # if interview is Non show select EA form
        if interview is None and access.interviewer.unfinished_assignments.exists() and \
                access.interviewer.unfinished_assignments.first().survey.is_open() is False:  # make sure survey is open
            template_file = 'interviews/no-open-survey.html'
            context = {'button_label': 'send',
                       'template_file': template_file,
                       'access': access,
                       'id': 'interview_form',
                       'action': self.action_url
                       }
            if show_only_answer_form(request):
                context['display_format'] = get_display_format(request)
                return render(request, template_file, context)
            return render(request, 'interviews/new.html', context)
        else:
            return super(OnlineInterview, self).respond(request, session_data)

    def start_interview(self, request, session_data):
        """Steps:
        1. Select EA
        2`. Select Batch if survey is ready for batch collection, else skip this step and select available listing/batch
        3. Move to interview questions.
        This func is expected to be called only when survey is open
        :param self:
        :param request:
        :param session_data:
        :return:
        """
        access = self.access
        interviewer = access.interviewer
        request_data = request.GET if request.method == 'GET' else request.POST
        if '_interview' in session_data:      # this options comes when there are multiple batches to choose from
            survey = session_data['_interview'].survey
            interview_form = SelectBatchForm(request, access, survey, data=request_data)
            if interview_form.is_valid():
                batch = interview_form.cleaned_data['batch']
                interview = session_data['_interview']
                interview.question_set = batch
                interview.last_question = batch.g_first_question
                del session_data['_interview']
                return self.init_responses(request, interview, session_data)
        elif 'interview' in session_data:       # though the interview value would be None
            interview_form = SurveyAllocationForm(request, access, data=request_data)
            if interview_form.is_valid():
                interview = interview_form.save(commit=False)
                interview.interviewer = interviewer
                interview.interview_channel = access
                survey = interview.survey
                survey_allocation = interview_form.selected_allocation()
                if interview.survey.has_sampling and (SurveyAllocation.can_start_batch(interviewer) is False):
                    # go straight to listing form
                    listing_form = survey.listing_form
                    if listing_form is None:    # assuming preferred listing did not cover completed for allocated ea
                        listing_form = survey.preferred_listing.listing_form
                    interview.question_set = listing_form
                    interview.last_question = listing_form.g_first_question
                    return self.init_responses(request, interview, session_data)
                else:
                    # ask user to select the batch if batch is more than one
                    if len(survey_allocation.open_batches()) > 1:
                        session_data['_interview'] = interview      # semi formed, ask user to choose batch
                        interview_form = SelectBatchForm(request, access, survey)
                    else:
                        batch = survey_allocation.open_batches()[0]
                        interview.question_set = batch
                        interview.last_question = batch.g_first_question
                        return self.init_responses(request, interview, session_data)
        else:
            interview_form = SurveyAllocationForm(request, access)
        session_data['interview'] = None
        template_file = "interviews/answer.html"
        context = {'button_label': 'send', 'answer_form': interview_form,
                   'template_file': template_file,
                   'access': access,
                   'id': 'interview_form',
                   'action': self.action_url
                   }
        if show_only_answer_form(request):
            context['display_format'] = get_display_format(request)
            return render(request, template_file, context)
        return render(request, 'interviews/new.html', context)
