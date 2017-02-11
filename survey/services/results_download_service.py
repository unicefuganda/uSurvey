import pandas as pd
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from survey.models import LocationTypeDetails, Location, LocationType, Household, HouseholdMember, \
    HouseholdMemberGroup, Answer, MultiChoiceAnswer, MultiSelectAnswer, NumericalAnswer, QuestionOption, Interview
from survey.utils.views_helper import get_ancestors
from survey.utils.query_helper import to_df
from datetime import datetime
import csv
import StringIO
import string
from collections import OrderedDict
import dateutils
from survey.odk.utils.log import logger


class ResultComposer:

    def __init__(self, user, results_download_service):
        self.results_download_service = results_download_service
        self.user = user

    def send_mail(self):
        attachment_name = '%s.csv' % (self.results_download_service.batch.name if self.results_download_service.batch
                                      else self.results_download_service.survey.name)
        subject = 'Completion report for %s' % attachment_name
        text = 'Completion report for %s. Date: %s' % (
            attachment_name, datetime.now())
        print 'commencing...'
        try:
            mail = EmailMessage(subject, text, settings.DEFAULT_EMAIL_SENDER, [
                                self.user.email, ])
            results_df = self.get_interview_answers()
            f = StringIO.StringIO()
            data = results_df.to_csv(f, columns=results_df.columns[1:])   #exclude interview id
            f.seek(0)
            mail.attach(attachment_name, f.read(), 'text/csv')
            f.close()
            sent = mail.send()
            print 'Emailed!! ', sent
        except Exception, ex:
            print 'error while sending mail: %s', str(ex)


class ResultsDownloadService(object):
    AS_TEXT = 1
    AS_LABEL = 0
    answers = None

    def __init__(self, survey=None, batch=None, restrict_to=None, interviews=None, multi_display=AS_TEXT):
        self.batch = batch
        self.locations = []
        if restrict_to:
            map(lambda loc: self.locations.extend(
                loc.get_leafnodes(include_self=True)), restrict_to)
        self.interviews = interviews
        self.multi_display = int(multi_display)

    def get_interview_answers(self):
        interview_list_args = ['created', 'ea__locations__name', 'ea__name', 'id', ]
        parent_loc = 'ea__locations'
        for i in range(LocationType.objects.count() - 2):
            parent_loc = '%s__parent' % parent_loc
            interview_list_args.insert(1, '%s__name' % parent_loc)
        interview_filter_args = {'question_set': self.batch}
        if self.locations:
            interview_filter_args['ea__locations__in'] = self.locations
        interview_query_args = list(interview_list_args)
        answer_query_args = ['interview__id', 'identifier', ]
        value = 'as_text'
        if self.multi_display == self.AS_LABEL:
            value = 'as_value'
        answer_query_args.append(value)
        answers_filter_args = {'question__qset__pk': self.batch.pk}
        if self.interviews:
            interview_queryset = self.interviews
            answers_filter_args['interview__in'] = self.interviews
        else:
            interview_queryset = Interview.objects
        interview_queryset= interview_queryset.filter(**interview_filter_args).values_list(*interview_query_args)
        answers_queryset = Answer.objects.filter(**answers_filter_args).values_list(*answer_query_args)
        interviews_df = to_df(interview_queryset, date_cols=['created'])
        answers_df = to_df(answers_queryset)
        # not get pivot table of interview_id, identifier and question value
        answers_report_df = answers_df.pivot(index='id', columns='identifier', values=value)
        reports_df = interviews_df.join(answers_report_df, on='id', how='outer')
        header_names = ['Interview_id', 'Created', ]
        location_names = list(LocationType.objects.get(parent__isnull=True).get_descendants(include_self=False))
        header_names.extend(location_names)
        header_names.append('EA')
        header_names.extend(list(reports_df.columns)[len(header_names):])
        reports_df.columns = header_names
        reports_df = reports_df.groupby(['Created', ]+location_names)
        return reports_df

    def generate_interview_reports(self):
        return self.get_interview_answers()

