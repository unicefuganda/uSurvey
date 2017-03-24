#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
import uuid
from django.utils import timezone
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from survey.models import (InterviewerAccess, QuestionLoop, QuestionSet, Answer, Question,
                           SurveyAllocation, AnswerAccessDefinition, ODKAccess, Interviewer, Interview)
from survey.forms.answer import (get_answer_form, UserAccessForm, UssdTimeoutForm,
                                 SurveyAllocationForm, SelectBatchForm, AddMoreLoopForm)
from .utils import get_entry, set_entry, delete_entry
from survey.utils.logger import slogger


REQUEST_SESSION = 'req_session'


def get_display_format(request):
    request_data = request.GET if request.method == 'GET' else request.POST
    return request_data.get('format', 'html').lower()


def show_only_answer_form(request):
    return request.is_ajax() or get_display_format(request) == 'text'


class OnlineHandler(object):

    def __init__(self, access, action_url=""):
        self.access = access
        self.action_url = action_url

    def handle_session(self, request):
        """
        :param request
        :param access_id
        :return:
        """
        access = self.access
        slogger.debug('starting request with: %s' % locals())
        session_data = get_entry(access, REQUEST_SESSION, {})
        slogger.debug('fetched: %s. session data: %s' % (access.user_identifier, session_data))
        response = self.respond(request, session_data)
        slogger.debug('the session %s, data: %s' % (access.user_identifier, session_data))
        if session_data:
            set_entry(access, REQUEST_SESSION, session_data)
            slogger.debug('updated: %s session data: %s' % (access.interviewer, session_data))
        else:
            # session data has been cleared then remove the session space
            delete_entry(access)
            slogger.debug('removed: %s session data' % access.id)
        return response

    def respond(self, request, session_data):
        # check if there is any active interview, if yes, ask interview last question
        interview = session_data.get('interview', None)
        # if interview is Non show select EA form
        if interview is None:
            return self.start_interview(request, session_data)
        elif interview:
            return self.respond_interview(request, interview, session_data)

    def init_responses(self, request, interview, session_data):
        interview.save()
        session_data['interview'] = interview
        session_data['last_question'] = None
        session_data['answers'] = {}
        session_data['loops'] = {}
        return self.respond(request, session_data)

    def start_interview(self, request, session_data):
        """To be implemented by implementors
        :param request:
        :param session_data:
        :return:
        """
        pass

    def respond_interview(self, request, interview, session_data):
        initial = {}
        answer = None
        access = self.access
        request_data = request.GET if request.method == 'GET' else request.POST
        if hasattr(interview.last_question, 'loop_started'):
            initial = {'value': session_data['loops'].get(interview.last_question.loop_started.id, 1)}
            if 'value' in request_data:
                request_data = request_data.copy()
                request_data['value'] = initial['value']
        if str(session_data['last_question']) == str(interview.last_question.id):
            answer_form = get_answer_form(interview, access)(request_data, request.FILES)
            if answer_form.is_valid():
                commit = True
                answer = answer_form.save()     # even for test data, to make sure the answer can actually save
                # decided to keep both as text and as value
                session_data['answers'][interview.last_question.identifier] = answer
                next_question = self.get_loop_next(request, interview, session_data)
                if next_question is None:
                    next_question = self.get_group_aware_next(request, answer, interview, session_data)
                if next_question is None:
                    interview.closure_date = timezone.now()
                    session_data['last_question'] = None
                else:
                    interview.last_question = next_question
                interview.save()
                return self.respond(request, session_data)
        else:
            answer_form = get_answer_form(interview, access)(initial=initial)
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
        if 'prompt_user_loop' in session_data.get('loops', []):
            answer_form = AddMoreLoopForm(request, access)
        context = {'title': "%s Survey" % interview.survey,
                   'button_label': 'send', 'answer_form': answer_form,
                   'interview': interview,
                   'survey': interview.survey,
                   'access': access,
                   # for display, use answer as text. Answer as value is used for group and question logic
                   'existing_answers': session_data.get('answers', {}),
                   'loops': session_data.get('loops', []),
                   'template_file': template_file,
                   'id': 'interview_form',
                   'action': self.action_url,
                   'timeout_form': UssdTimeoutForm()
                   }
        if show_only_answer_form(request):
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
            else:   # user selected loop
                request_data = request.POST if request.method == 'POST' else request.GET
                # some funky logic here.
                # if it's a user selected loop, session attribute add_loop is set.
                # if so, attempt to validate, the selection and accordingly repeat loop or not.
                # else set the add_loop attribute. And provide the loop form needed for validation
                if loop.repeat_logic is None:
                    if 'prompt_user_loop' in session_data.get('loops', []):
                        add_more_form = AddMoreLoopForm(request, self.access, data=request_data)
                        if add_more_form.is_valid():
                            if int(add_more_form.cleaned_data['value']) == AddMoreLoopForm.ADD_MORE:
                                loop_next = loop.loop_starter
                            else:
                                loop_next = None
                            del session_data['loops']['prompt_user_loop']
                    else:
                        session_data['loops']['prompt_user_loop'] = loop.loop_prompt
            if 'prompt_user_loop' in session_data.get('loops', []):     # if you have to prompt the user to cont loop...
                loop_next = loop.loop_ender         # stay at last loop question
                session_data['last_question'] = None
            elif loop_next:     # not prompt
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
        access = self.access

        def _get_group_next_question(question, proposed_next):
            next_question = proposed_next
            present_question_group = question.group if hasattr(question, 'group') else None
            if next_question and AnswerAccessDefinition.is_valid(access.choice_name(),
                                                                 next_question.answer_type) is False:
                next_question = _get_group_next_question(question, next_question.next_question(answer.as_value))
            # I hope the next line is not so confusing!
            # Basically it means treat only if the next question belongs to a different group from the present.
            # That's if present has a group
            if hasattr(next_question, 'group') and present_question_group != next_question.group:
                question_group = next_question.group
                if question_group:
                    qset = QuestionSet.get(pk=next_question.qset.pk)
                    valid_group = True
                    for condition in question_group.group_conditions.all():
                        # we are interested in the qset param list with same identifier name as condition.test_question
                        test_question = qset.parameter_list.questions.get(identifier=condition.test_question.identifier)
                        param_value = ''            # use answer.as value
                        if session_data['answers'].get(test_question.identifier, None):
                            param_value = session_data['answers'][test_question.identifier].as_value
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
                        next_question = _get_group_next_question(question, next_question.next_question(answer.as_value))
            return next_question
        return _get_group_next_question(interview.last_question,
                                        interview.last_question.next_question(answer.as_value))