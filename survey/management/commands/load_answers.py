#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'
import pandas as pd
from django.core.management.base import BaseCommand
from survey.models import QuestionSet, Survey, Interview, Answer
from survey.models import EnumerationArea
from survey.models import Interviewer


def save_interview(row, interviewer, odk_access, survey, qset, questions, eas={}):
    try:
        ea = eas.get(row['ea'], None)
        if ea is None:
            ea = EnumerationArea.objects.get(pk=row['ea'])
            eas[row['ea']] = ea
        interview = Interview.objects.create(question_set=qset, survey=survey,
                                             ea=ea, interview_channel=odk_access)
        map(lambda question: Answer.get_class(question.answer_type).create(interview, question,
                                                                           row[question.identifier]),
            questions)
    except Exception, ex:
        pass


class Command(BaseCommand):
    args = 'name_of_the_csv.file interviewer_id survey_id, qset_id'
    help = 'loads '

    def handle(self, *args, **kwargs):
        """Basically loads each line of the csv as9 responses to the question set
        each row is seen as a seperate interview.9
        first field would be the ea ID, subsequent fields would be the answers9
        :param args:
        :param kwargs:
        :return:
        """
        self.stdout.write('Starting...')
        delimiter = kwargs.get('delim', ',')
        df = pd.read_csv(args[0], delimiter=delimiter)
        interviewer = Interviewer.get(pk=args[1])
        survey = Survey.get(pk=args[2])
        qset = QuestionSet.get(pk=int(args[3]))
        odk_access = interviewer.odk_access[0]
        all_questions = qset.all_questions
        eas = {}
        #>with transaction.atomic():
        df.apply(save_interview, axis=1, args=(interviewer, odk_access, survey, qset, all_questions, eas))
        self.stdout.write('Successfully imported!')

