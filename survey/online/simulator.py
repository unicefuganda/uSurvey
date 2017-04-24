#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from survey.models import QuestionSet, ODKAccess, Interview
from online_handler import OnlineHandler


class MockAccess(object):
    """This is just used to mock an interviewer access.
    """
    interviewer = None

    def __init__(self, request, qset, access_type=ODKAccess.choice_name()):
        self.id = 'test: %s, %s' % (request.user.username, qset.id)
        self.question_set = QuestionSet.get(id=qset.id)
        self.user_identifier = self.id
        self.access_type = access_type

    def choice_name(self):
        return self.access_type


@login_required
def handle_request(request, qset_id):
    qset = QuestionSet.get(id=qset_id)
    request_data = request.GET if request.method == 'GET' else request.POST
    mock_access = MockAccess(request, qset)
    if 'uid' in request_data:
        mock_access.id = str(request_data['uid'])
    handler = SimulatorView(
        mock_access,
        action_url=reverse(
            'test_qset_flow',
            args=(qset_id, )))
    return handler.handle_session(request)


class SimulatorView(OnlineHandler):

    def start_interview(self, request, session_data):
        """Just create a mock interview and move on.
        :param self:
        :param request:
        :param session_data:
        :return:
        """
        access = self.access
        if hasattr(access, 'question_set'):
            interview = Interview(test_data=True, question_set=access.question_set,
                                  last_question=access.question_set.g_first_question)
            session_data['interview'] = interview
            return self.init_responses(request, interview, session_data)
