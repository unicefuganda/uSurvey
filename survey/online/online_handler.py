#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
from django.utils import timezone
from collections import OrderedDict
from copy import deepcopy
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from survey.models import (InterviewerAccess, QuestionLoop, QuestionSet, Answer, Question, QuestionOption,
                           SurveyAllocation, AnswerAccessDefinition, ODKAccess, Interviewer, Interview)
from survey.forms.answer import (get_answer_form, UserAccessForm, UssdTimeoutForm,
                                 SurveyAllocationForm, SelectBatchForm, AddMoreLoopForm)
from .utils import get_entry, set_entry, delete_entry
from survey.utils.logger import slogger


REQUEST_SESSION = 'req_session'
PREVIOUS_QUESTIONS = 'previous_questions'
LAST_QUESTION = 'last_question'
LOOPS = 'loops'
REF_INTERVIEW = 'ref_interview'
INTERVIEW = 'interview'
ANSWERS = 'answers'
COUNT = 'count'
PROMPT_USER_LOOP = 'prompt_user_loop'


def get_display_format(request):
    request_data = request.GET if request.method == 'GET' else request.POST
    return request_data.get('format', 'html').lower()


def show_only_answer_form(request):
    return request.is_ajax() or get_display_format(request) == 'text'


def restart(request, access_id):
    access = InterviewerAccess.get(id=access_id)
    delete_entry(access)
    return HttpResponseRedirect(reverse('online_interviewer_view'))


class OnlineHandler(object):

    def __init__(self, access, action_url=""):
        self.access = access
        self.action_url = action_url

    def handle_session(self, request):
        """
        :param self
        :param request
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
        interview = session_data.get(INTERVIEW, None)
        # if interview is Non show select EA form
        if interview is None:
            return self.start_interview(request, session_data)
        elif interview:
            return self.respond_interview(request, interview, session_data)

    def _save_answers(self, request, session_data, navigation_interview):
        answers = session_data[ANSWERS]
        reference_interview = session_data.get(REF_INTERVIEW, None)
        qset = QuestionSet.get(pk=navigation_interview.question_set.pk)
        question_map = dict([(q.identifier, q) for q in qset.all_questions])
        survey = navigation_interview.survey
        ea = navigation_interview.ea
        Interview.save_answers(qset, survey, ea, navigation_interview.interview_channel, question_map, answers,
                               reference_interview=reference_interview)

    def _update_answer(self, request, session_data, question, answer):
        if session_data[LOOPS][COUNT].keys():       # basically check if there are ongoing loops
            session_data[ANSWERS][-1].update({question.identifier: answer})
        else:
            map(lambda answer_dict: answer_dict.update({question.identifier: answer}), session_data[ANSWERS])

    def _add_loop_answer_entry(self, request, loop, session_data):
        """Each loop entry is stored as in seperate row for ease of reporting
        :param request:
        :param session_data:
        :return:
        """
        last_answer_dict = session_data[ANSWERS][-1]
        loop_answers_row = deepcopy(last_answer_dict)
        # clear entries belonging to this loop, to avoid old loop responses on a new loop
        map(lambda question: loop_answers_row.update({question.identifier: ''}), loop.loop_questions())
        session_data[ANSWERS].append(loop_answers_row)

    def init_responses(self, request, interview, session_data):
        #interview.save()
        session_data[INTERVIEW] = interview       # This interview is only used for question navigation purposes
        session_data[LAST_QUESTION] = None
        session_data[PREVIOUS_QUESTIONS] = []
        session_data[ANSWERS] = [{}, ]
        session_data[LOOPS] = {COUNT: OrderedDict(), }
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
        has_go_back = 'has-go-back' in request_data
        if hasattr(interview.last_question, 'loop_started'):
            initial = {'value': session_data[LOOPS][COUNT].get(interview.last_question.loop_started.id, 1)}
            if 'value' in request_data:
                request_data = request_data.copy()
                request_data['value'] = initial['value']
        if 'go-back' in request_data:
            # fail naturally if there is not previous question
            questions = session_data[PREVIOUS_QUESTIONS]
            interview.last_question = questions.pop()     # just pick the last previous
            session_data[PREVIOUS_QUESTIONS] = questions
            answer_form = get_answer_form(interview, access)(initial=initial)
            session_data[LAST_QUESTION] = interview.last_question.id
            has_go_back = True
        elif str(session_data[LAST_QUESTION]) == str(interview.last_question.id):
            answer_form = get_answer_form(interview, access)(request_data, request.FILES)
            if answer_form.is_valid():
                # answer = answer_form.save()     # even for test data, to make sure the answer can actually save
                # decided to keep both as text and as value
                self._update_answer(request, session_data, interview.last_question,
                                    answer_form.cleaned_data['value'])           # update in session
                next_question = self.get_loop_next(request, interview, session_data)
                if next_question is None:
                    next_question = self.get_group_aware_next(request, answer_form.cleaned_data['value'],
                                                              interview, session_data)
                if next_question is None:
                    interview.closure_date = timezone.now()
                    session_data[LAST_QUESTION] = None
                    if interview.test_data is False:
                        self._save_answers(request, session_data, interview)    # save when entire questions are asked
                else:
                    # do not include same question following itself
                    if interview.last_question and \
                            (len(session_data[PREVIOUS_QUESTIONS]) == 0
                             or session_data[PREVIOUS_QUESTIONS][-1].pk != interview.last_question.pk):
                        questions = session_data[PREVIOUS_QUESTIONS]
                        questions.append(interview.last_question)
                        session_data[PREVIOUS_QUESTIONS] = questions
                    interview.last_question = next_question
                return self.respond(request, session_data)
        else:
            answer_form = get_answer_form(interview, access)(initial=initial)
            session_data[LAST_QUESTION] = interview.last_question.id
        if interview.closure_date:
            template_file = "interviews/completed.html"
            del session_data[INTERVIEW]
            del session_data[PREVIOUS_QUESTIONS]
            if ANSWERS in session_data:
                del session_data[ANSWERS]
            if LOOPS in session_data:
                del session_data[LOOPS]
            if LAST_QUESTION in session_data:
                del session_data[LAST_QUESTION]
        else:
            template_file = "interviews/answer.html"
        if PROMPT_USER_LOOP in session_data.get(LOOPS, []):
            answer_form = AddMoreLoopForm(request, access)
        context = {'title': "%s Survey" % interview.survey,
                   'button_label': 'send', 'answer_form': answer_form,
                   INTERVIEW: interview,
                   'survey': interview.survey,
                   'has_go_back': has_go_back,
                   'access': access,
                   'ussd_session_timeout': settings.USSD_TIMEOUT,
                   # for display, use answer as text. Answer as value is used for group and question logic
                   'existing_answers': session_data.get(ANSWERS, {}),
                   LOOPS: session_data.get(LOOPS, []),
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
        if hasattr(interview.last_question, 'loop_started'):
            loop_id = interview.last_question.loop_started.id
            if loop_id not in session_data[LOOPS][COUNT]:
                session_data[LOOPS][COUNT][loop_id] = 1
        elif hasattr(interview.last_question, 'loop_ended'):
            loop = interview.last_question.loop_ended
            count = session_data[LOOPS][COUNT].get(loop.id, 1)

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
                    if PROMPT_USER_LOOP in session_data.get(LOOPS, {}):
                        add_more_form = AddMoreLoopForm(request, self.access, data=request_data)
                        if add_more_form.is_valid():
                            if int(add_more_form.cleaned_data['value']) == AddMoreLoopForm.ADD_MORE:
                                loop_next = loop.loop_starter
                            else:
                                loop_next = None
                            del session_data[LOOPS][PROMPT_USER_LOOP]
                    else:
                        session_data[LOOPS][PROMPT_USER_LOOP] = loop.loop_prompt
            if PROMPT_USER_LOOP in session_data.get(LOOPS, []):     # if you have to prompt the user to cont loop...
                loop_next = loop.loop_ender         # stay at last loop question
                session_data[LAST_QUESTION] = None
            elif loop_next:     # not prompt
                # update answers with new loop row
                session_data[LOOPS][COUNT][loop.id] = count + 1
                self._add_loop_answer_entry(request, loop, session_data)     # add another entry every extra loop
            elif loop.id in session_data[LOOPS][COUNT]:
                del session_data[LOOPS][COUNT][loop.id]
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
        if isinstance(answer, QuestionOption):
            reply = answer.order
        else:
            reply = answer

        def _get_group_next_question(question, proposed_next):
            next_question = proposed_next
            present_question_group = question.group if hasattr(question, 'group') else None
            if next_question and AnswerAccessDefinition.is_valid(access.choice_name(),
                                                                 next_question.answer_type) is False:
                next_question = _get_group_next_question(question, next_question.next_question(reply))
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
                        if session_data[ANSWERS][-1].get(test_question.identifier, None):    # last answer entry
                            param_value = session_data[ANSWERS][-1][test_question.identifier]
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
                        next_question = _get_group_next_question(question, next_question.next_question(reply))
            return next_question
        return _get_group_next_question(interview.last_question,
                                        interview.last_question.next_question(reply))