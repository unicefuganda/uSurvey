#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from survey.models import Interview, Interviewer, InterviewerAccess, WebAccess, QuestionLoop, AutoResponse
from survey.forms.answer import get_answer_form, SelectInterviewForm
from .utils import get_entry, set_entry, delete_entry
from .logger import slogger

REQUEST_SESSION = 'req_session'

@login_required
def handle_session(request, access_id):
    '''
    :param request
    :param interviewer_id
    :return:
    '''
    access = InterviewerAccess.get(id=access_id)
    slogger.debug('starting request with: %s' % locals())
    session_data = get_entry(access.interviewer, REQUEST_SESSION, {})
    slogger.info('fetched: %s. session data: %s' % (access.user_identifier, session_data))
    response = respond(access, request, session_data)
    slogger.info('the session %s, data: %s' % (access.user_identifier, session_data))
    if session_data:
        set_entry(access.interviewer, REQUEST_SESSION, session_data)
        slogger.info('updated: %s session data: %s' % (access.interviewer, session_data))
    else:
        #session data has been cleared then remove the session space
        delete_entry(access.interviewer)
        slogger.info('removed: %s session data' % access.interviewer.pk)
    return response


def respond(access, request, session_data):
    interviewer = access.interviewer
    # check if there is any active interview, if yes, ask interview froquestion
    interview = session_data.get('interview')
    # if interview is Non show select EA form
    if interview is None:
        return make_interview(request, access, session_data)
    elif interview:
        return respond_interview(request, interview, session_data)


def make_interview(request, access, session_data):
    interviewer = access.interviewer
    if request.method == 'POST':
        interview_form = SelectInterviewForm(interviewer, data=request.POST)
        if interview_form.is_valid():
            interview = interview_form.save(commit=False)
            interview.interviewer = interviewer
            interview.interview_channel = access
            interview.last_question = interview.question_set.start_question
            interview.save()
            session_data['interview'] = interview
            session_data['answers'] = {}
            session_data['loops'] = {}
            return HttpResponseRedirect('.')
    else:
        interview_form = SelectInterviewForm(interviewer)
    template_file = "interviews/answer.html"
    context = {
               'button_label': 'send',
                'answer_form' : interview_form,
                'template_file': template_file,
                'access': access,
                'id' : 'interview_form',
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
            last_question = interview.last_question
            next_question = last_question.next_question(answer.to_text())
            if next_question is None:
                interview.closure_date = timezone.now()
            else:
                interview.last_question = next_question
            sync_loop(request, interview, last_question, session_data)
            interview.save()
            if hasattr(interview.last_question, 'loop_started'):
                initial = {'value': session_data['loops'].get(interview.last_question.loop_started.id, 1)}
            answer_form = get_answer_form(interview)(initial=initial)
    else:
        if hasattr(interview.last_question, 'loop_started'):
            initial = {'value': session_data['loops'].get(interview.last_question.loop_started.id, 1)}
        answer_form = get_answer_form(interview)(initial={})
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


def sync_loop(request, interview, prev_question, session_data):
    if hasattr(prev_question, 'loop_ended'):
        loop = prev_question.loop_ended
        count = session_data['loops'].get(loop.id, 1)
        if loop.repeat_logic in [QuestionLoop.FIXED_REPEATS, QuestionLoop.PREVIOUS_QUESTION]:
            if loop.repeat_logic == QuestionLoop.FIXED_REPEATS:
                max_val = loop.fixedloopcount.value
            if loop.repeat_logic == QuestionLoop.PREVIOUS_QUESTION:
                max_val = loop.previousanswercount.get_count(interview)
            if max_val > count:
                interview.last_question = loop.loop_starter
                session_data['loops'][loop.id] = count + 1
                return True
            elif session_data['loops'].has_key(loop.id):
                del session_data['loops'][loop.id]
        if loop.repeat_logic == QuestionLoop.USER_DEFINED:
            add_loop = session_data.get('add_loop', False)
            if add_loop:
                interview.last_question = loop.loop_starter
                return True
            elif session_data.has_key('add_loop'):
                del session_data['add_loop']
        return False





