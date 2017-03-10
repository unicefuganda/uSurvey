#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from survey.models import (InterviewerAccess, QuestionLoop, QuestionSet, Answer, Question)
from survey.forms.answer import get_answer_form, SelectInterviewForm
from .utils import get_entry, set_entry, delete_entry
from survey.utils.logger import slogger

REQUEST_SESSION = 'req_session'


@login_required
def handle_session(request, access_id):
    """
    :param request
    :param access_id
    :return:
    """
    access = InterviewerAccess.get(id=access_id)
    slogger.debug('starting request with: %s' % locals())
    session_data = get_entry(access, REQUEST_SESSION, {})
    slogger.info('fetched: %s. session data: %s' % (access.user_identifier, session_data))
    response = respond(access, request, session_data)
    slogger.info('the session %s, data: %s' % (access.user_identifier, session_data))
    if session_data:
        set_entry(access, REQUEST_SESSION, session_data)
        slogger.info('updated: %s session data: %s' % (access.interviewer, session_data))
    else:
        # session data has been cleared then remove the session space
        delete_entry(access)
        slogger.info('removed: %s session data' % access.pk)
    return response


def respond(access, request, session_data):
    interviewer = access.interviewer
    # check if there is any active interview, if yes, ask interview last question
    interview = session_data.get('interview')
    # if interview is Non show select EA form
    if interview is None:
        return start_interview(request, access, session_data)
    elif interview:
        return respond_interview(request, interview, session_data)


def start_interview(request, access, session_data):
    interviewer = access.interviewer
    if request.method == 'POST':
        interview_form = SelectInterviewForm(interviewer, data=request.POST)
        if interview_form.is_valid():
            interview = interview_form.save(commit=False)
            interview.interviewer = interviewer
            interview.interview_channel = access
            qset = QuestionSet.get(id=interview.question_set.id)       # distinquish listing from batch
            interview.last_question = qset.g_first_question
            interview.save()
            session_data['interview'] = interview
            session_data['answers'] = {}
            session_data['loops'] = {}
            return HttpResponseRedirect('.')
    else:
        interview_form = SelectInterviewForm(interviewer)
    template_file = "interviews/answer.html"
    context = {'button_label': 'send', 'answer_form': interview_form,
               'template_file': template_file,
               'access': access,
               'id': 'interview_form',
               }
    if request.is_ajax():
        return render(request, template_file, context)
    return render(request, 'interviews/new.html', context)


def respond_interview(request, interview, session_data):
    initial = {}
    if request.method == 'POST':
        answer_form = get_answer_form(interview)(request.POST, request.FILES)
        if answer_form.is_valid():
            answer = answer_form.save()
            session_data['answers'][interview.last_question.identifier] = answer.to_text()
            loop_next = get_loop_next(request, interview, session_data)      # gets next loop quest for interview
            if loop_next:
                next_question = loop_next
            else:
                next_question = get_group_aware_next(request, answer, interview, session_data)
            if next_question is None:
                interview.closure_date = timezone.now()
            else:
                interview.last_question = next_question
            interview.save()
            return HttpResponseRedirect('.')
    else:
        if hasattr(interview.last_question, 'loop_started'):
            initial = {'value': session_data['loops'].get(interview.last_question.loop_started.id, 1)}
        answer_form = get_answer_form(interview)(initial=initial)
    if interview.closure_date:
        template_file = "interviews/completed.html"
        del session_data['interview']
        if hasattr(session_data, 'answers'):
            del session_data['answers']
        if hasattr(session_data, 'loops'):
            del session_data['loops']
    else:
        template_file = "interviews/answer.html"
    context = {
               'title': "%s Survey" % interview.survey,
               'button_label': 'send',
                'answer_form' : answer_form,
                'interview' : interview,
                'survey': interview.survey,
                'existing_answers': session_data['answers'],
                'loops': session_data['loops'],
                'template_file': template_file,
                'id' : 'interview_form',
               }
    if request.is_ajax():
        return render(request, template_file, context)
    return render(request, 'interviews/new.html', context)


def get_loop_next(request, interview, session_data):
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
            if loop.repeat_logic is None and request_data.has_key('add_loop'):
                loop_next = loop.loop_starter
        if loop_next:
            session_data['loops'][loop.id] = count + 1
        elif session_data['loops'].has_key(loop.id):
            del session_data['loops'][loop.id]
        return loop_next


def get_group_aware_next(request, answer, interview, session_data):
    """Recursively check if next question is appropriate as per the respondent group
    Responded group would have been determined by the parameter list questions whose data is store in session_data
    :param request:
    :param answer:
    :param interview:
    :param session_data:
    :return:
    """

    def _get_group_next_question(question, proposed_next):
        next_question = proposed_next
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
                        is_valid = validator(param_value, *condition.test_params)
                    except:
                        is_valid = False
                    if is_valid is False:
                        valid_group = False
                        break   # fail if any condition fails
                if valid_group is False:
                    next_question = _get_group_next_question(question, next_question.next_question(answer.to_text()))
        return next_question
    return _get_group_next_question(interview.last_question, interview.last_question.next_question(answer.to_text()))





