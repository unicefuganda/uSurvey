#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
from django.utils import timezone
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from survey.models import (InterviewerAccess, QuestionLoop, QuestionSet, Answer, Question,
                           SurveyAllocation, AnswerAccessDefinition)
from survey.forms.answer import (get_answer_form, SelectInterviewForm, UserAccessForm,
                                 SurveyAllocationForm, SelectBatchForm)
from .utils import get_entry, set_entry, delete_entry
from survey.utils.logger import slogger

REQUEST_SESSION = 'req_session'


def get_display_format(request):
    request_data = request.GET if request.method == 'GET' else request.POST
    return request_data.get('format', 'html').lower()


def show_only_answer_form(request):
    return request.is_ajax() or get_display_format(request) == 'text'


@login_required
def get_access_details(request):
    request_data = request.GET if request.method == 'GET' else request.POST
    if 'uid' in request_data:
        access_form = UserAccessForm(data=request_data)
        if access_form.is_valid():
            access = access_form.cleaned_data['uid']
            return OnlineView(action_url=reverse('online_interviewer_view')).handle_session(request,
                                                                                            access_id=access.id)
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


def handle_session(request, access_id):
    online_view = OnlineView(action_url=reverse('online_view',
                                                args=(access_id, )))

    online_view.start_interview = start_qset_interview(online_view)
    return online_view.handle_session(request, access_id=access_id)


def start_qset_interview(online_view):
    def _start_interview(request, access, session_data):
        interviewer = access.interviewer
        request_data = request.GET if request.method == 'GET' else request.POST
        if 'interview' in session_data:
            interview_form = SelectInterviewForm(access, data=request_data)
            if interview_form.is_valid():
                interview = interview_form.save(commit=False)
                interview.interviewer = interviewer
                interview.interview_channel = access
                qset = QuestionSet.get(id=interview.question_set.id)       # distinquish listing from batch
                interview.last_question = qset.g_first_question
                return online_view.init_responses(request, interview, session_data)
        else:
            interview_form = SelectInterviewForm(access)
        session_data['interview'] = None
        template_file = "interviews/answer.html"
        context = {'button_label': 'send', 'answer_form': interview_form,
                   'template_file': template_file,
                   'access': access,
                   'id': 'interview_form',
                   }
        if show_only_answer_form(request):
            context['display_format'] = get_display_format(request)
            return render(request, template_file, context)
        return render(request, 'interviews/new.html', context)
    return _start_interview


def handle_interviewer_session(request, access_id=None):
    pass


class OnlineView(object):

    def __init__(self, action_url='', *rgs, **kwargs):
        self.action_url = action_url

    @method_decorator(login_required)
    def handle_session(self, request, access_id=None):
        """
        :param request
        :param access_id
        :return:
        """
        if access_id is None:
            uid = request.GET.get('uid') if request.method == 'GET' else request.POST.get('uid')
            access = InterviewerAccess.get(user_identifier=uid)
        else:
            access = InterviewerAccess.get(id=access_id)
        slogger.debug('starting request with: %s' % locals())
        session_data = get_entry(access, REQUEST_SESSION, {})
        slogger.info('fetched: %s. session data: %s' % (access.user_identifier, session_data))
        response = self.respond(access, request, session_data)
        slogger.info('the session %s, data: %s' % (access.user_identifier, session_data))
        if session_data:
            set_entry(access, REQUEST_SESSION, session_data)
            slogger.info('updated: %s session data: %s' % (access.interviewer, session_data))
        else:
            # session data has been cleared then remove the session space
            delete_entry(access)
            slogger.info('removed: %s session data' % access.pk)
        return response

    def respond(self, access, request, session_data):
        interviewer = access.interviewer
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
        elif interview is None:
            return self.start_interview(request, access, session_data)
        elif interview:
            return self.respond_interview(request, access, interview, session_data)

    def init_responses(self, request, interview, session_data):
        interview.save()
        session_data['interview'] = interview
        session_data['last_question'] = None
        session_data['answers'] = {}
        session_data['loops'] = {}
        return self.respond(interview.interview_channel, request, session_data)

    def start_interview(self, request, access, session_data):
        """Steps:
        1. Select EA
        2`. Select Batch if survey is ready for batch collection, else skip this step and select available listing/batch
        3. Move to interview questions.
        This func is expected to be called only when survey is open
        :param online_view:
        :param request:
        :param access:
        :param session_data:
        :return:
        """
        interviewer = access.interviewer
        request_data = request.GET if request.method == 'GET' else request.POST
        if '_interview' in session_data:      # this options comes when there are multiple batches to choose from
            survey = session_data['_interview'].survey
            interview_form = SelectBatchForm(access, survey, data=request_data)
            if interview_form.is_valid():
                batch = interview_form.cleaned_data['batch']
                interview = session_data['_interview']
                interview.question_set = batch
                interview.last_question = batch.g_first_question
                del session_data['_interview']
                return self.init_responses(request, interview, session_data)
        elif 'interview' in session_data:       # though the interview value would be None
            interview_form = SurveyAllocationForm(access, data=request_data)
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
                        interview_form = SelectBatchForm(access, survey)
                    else:
                        batch = survey_allocation.open_batches()[0]
                        interview.question_set = batch
                        interview.last_question = batch.g_first_question
                        return self.init_responses(request, interview, session_data)
        else:
            interview_form = SurveyAllocationForm(access)
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

    def respond_interview(self, request, access, interview, session_data):
        initial = {}
        request_data = request.GET if request.method == 'GET' else request.POST
        if str(session_data['last_question']) == str(interview.last_question.id):
            answer_form = get_answer_form(interview)(request_data, request.FILES)
            if answer_form.is_valid():
                commit = True
                answer = answer_form.save()     # even for test data, to make sure the answer can actually save
                session_data['answers'][interview.last_question.identifier] = answer.to_text()
                loop_next = self.get_loop_next(request, interview, session_data)      # gets next loop quest for interview
                if loop_next:
                    next_question = loop_next
                else:
                    next_question = self.get_group_aware_next(request, answer, interview, session_data)
                if next_question is None:
                    interview.closure_date = timezone.now()
                    session_data['last_question'] = None
                else:
                    interview.last_question = next_question
                interview.save()
                return self.respond(interview.interview_channel, request, session_data)
        else:
            if hasattr(interview.last_question, 'loop_started'):
                initial = {'value': session_data['loops'].get(interview.last_question.loop_started.id, 1)}
            answer_form = get_answer_form(interview)(initial=initial)
            session_data['last_question'] = interview.last_question.id
        if interview.closure_date:
            if interview.test_data:
                interview.delete()
            template_file = "interviews/completed.html"
            del session_data['interview']
            if 'answers' in session_data:
                del session_data['answers']
            if 'loops' in session_data:
                del session_data['loops']
            if 'last_question' in session_data:
                del session_data['last_question']
        else:
            template_file = "interviews/answer.html"
        context = {'title': "%s Survey" % interview.survey,
                   'button_label': 'send', 'answer_form': answer_form,
                   'interview': interview,
                   'survey': interview.survey,
                   'access': access,
                   'existing_answers': session_data.get('answers', []),
                   'loops': session_data.get('loops', []),
                   'template_file': template_file,
                   'id': 'interview_form',
                   'action': self.action_url

                   }

        if show_only_answer_form(request):
            #>import pdb; pdb.set_trace()
            context['display_format'] = get_display_format(request)
            return render(request, template_file, context)
        return render(request, 'interviews/new.html', context)

    def get_loop_next(self, request, interview, session_data):
        if hasattr(interview.last_question, 'loop_ended'):
            loop = interview.last_question.loop_ended
            count = session_data['loops'].get(loop.id, 1)
            loop_next = None
            if loop.repeat_logic in [QuestionLoop.FIXED_REPEATS, QuestionLoop.PREVIOUS_QUESTION]:
                if loop.repeat_logic == QuestionLoop.FIXED_REPEATS:
                    max_val = loop.fixedloopcount.value
                if loop.repeat_logic == QuestionLoop.PREVIOUS_QUESTION:
                    max_val = loop.previousanswercount.get_count(interview)
                if max_val > count:
                    loop_next = loop.loop_starter
            else:
                request_data = request.POST if request.method == 'POST' else request.GET
                if loop.repeat_logic is None and 'add_loop' in request_data:
                    loop_next = loop.loop_starter
            if loop_next:
                session_data['loops'][loop.id] = count + 1
            elif loop.id in session_data['loops']:
                del session_data['loops'][loop.id]
            return loop_next

    def get_group_aware_next(self, request, answer, interview, session_data):
        """Recursively check if next question is appropriate as per the respondent group
        Responded group would have been determined by the parameter list questions whose data is store in session_data
        :param request:
        :param answer:
        :param interview:
        :param session_data:
        :return:
        """
        access = InterviewerAccess.get(pk=interview.interview_channel.pk)
        def _get_group_next_question(question, proposed_next):
            next_question = proposed_next
            if next_question and AnswerAccessDefinition.is_valid(access.choice_name(),
                                                                 next_question.answer_type) is False:
                next_question = _get_group_next_question(question, next_question.next_question(answer.to_text()))
            if hasattr(question, 'group') and hasattr(next_question, 'group') \
                    and question.group != next_question.group:
                question_group = next_question.group
                if question_group:
                    qset = QuestionSet.get(pk=question.qset.pk)
                    valid_group = True
                    for condition in question_group.group_conditions.all():
                        # we are interested in the qset param list with same identifier name as condition.test_question
                        test_question = qset.parameter_list.questions.get(identifier=condition.test_question.identifier)
                        param_value = session_data['answers'].get(test_question.identifier, '')
                        answer_class = Answer.get_class(condition.test_question.answer_type)
                        validator = getattr(answer_class, condition.validation_test, None)
                        if validator is None:
                            raise ValueError('unsupported validator defined on listing question')
                        try:
                            slogger.debug('parm val: %s, params: %s' % (param_value, condition.test_params))
                            is_valid = validator(param_value, *condition.test_params)
                        except:
                            is_valid = True
                        if is_valid is False:
                            valid_group = False
                            break   # fail if any condition fails
                    if valid_group is False:
                        next_question = _get_group_next_question(question, next_question.next_question(answer.to_text()))
            return next_question
        return _get_group_next_question(interview.last_question,
                                        interview.last_question.next_question(answer.to_text()))





