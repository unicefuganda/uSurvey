from datetime import date
from survey.models.locations import *
from survey.models import *
from survey.services.results_download_service import ResultsDownloadService
from survey.tests.base_test import BaseTest
from survey.tests.models.survey_base_test import SurveyBaseTest


class ResultsDownloadServiceTest(SurveyBaseTest):

    def _prep_answers(self):
        self._create_test_non_group_questions(self.qset)
        answers = []
        n_quest = Question.objects.get(answer_type=NumericalAnswer.choice_name())
        t_quest = Question.objects.get(answer_type=TextAnswer.choice_name())
        m_quest = Question.objects.get(answer_type=MultiChoiceAnswer.choice_name())
        # first is numeric, then text, then multichioice
        answers = [{n_quest.id: 1, t_quest.id: 'Hey Man', m_quest.id: 'Y'},
                   {n_quest.id: 5, t_quest.id: 'Our Hey Boy', m_quest.id: 'Y'},
                   {n_quest.id: 27, t_quest.id: 'Hey Girl!', m_quest.id: 'N'},
                   {n_quest.id: 12, t_quest.id: 'Hey Raster!', m_quest.id: 'N'},
                   {n_quest.id: 19, t_quest.id: 'This bad boy'}
                   ]
        question_map = {n_quest.id: n_quest, t_quest.id: t_quest, m_quest.id: m_quest}
        interview = self.interview
        interviews = Interview.save_answers(self.qset, self.survey, self.ea,
                                            self.access_channel, question_map, answers)
        # confirm that 11 answers has been created
        self.assertEquals(NumericalAnswer.objects.count(), 5)
        self.assertEquals(TextAnswer.objects.count(), 5)
        self.assertEquals(MultiChoiceAnswer.objects.count(), 4)
        self.assertEquals(TextAnswer.objects.first().to_text().lower(), 'Hey Man'.lower())
        self.assertEquals(MultiChoiceAnswer.objects.first().as_text.lower(), 'Y'.lower())
        multichoice = MultiChoiceAnswer.objects.first()
        self.assertEquals(multichoice.as_value,
                          str(QuestionOption.objects.get(text='Y', question=multichoice.question).order))
        return Interview.objects.filter(id__in=[i.id for i in interviews])

    def test_reference_interview_report(self):
        self._prep_answers()
        ref_interview = Interview.objects.last()
        self._create_ussd_non_group_questions(self.qset1)
        n_quest = Question.objects.filter(answer_type=NumericalAnswer.choice_name(),
                                          qset=self.qset1).last()
        t_quest = Question.objects.filter(answer_type=TextAnswer.choice_name(),
                                          qset=self.qset1).last()
        m_quest = Question.objects.filter(answer_type=MultiChoiceAnswer.choice_name(),
                                          qset=self.qset1).last()
        answers = [{n_quest.id: 27, t_quest.id: 'Test Ref', m_quest.id: 'N'},
                   ]
        question_map = {n_quest.id: n_quest, t_quest.id: t_quest, m_quest.id: m_quest}
        interviews = Interview.save_answers(self.qset1, self.survey, self.ea,
                                            self.access_channel, question_map, answers,
                                            reference_interview=ref_interview)
        rs = ResultsDownloadService(self.qset1, survey=self.survey, follow_ref=True)
        reports_df = rs.generate_interview_reports()
        for answer in ref_interview.answer.all():
            # since this ref_interview only captured one row of information, so this is valid
            self.assertEquals(answer.as_text, reports_df[answer.question.identifier][0])
        for answer in interviews[0].answer.all():
            # since this ref_interview only captured one row of information, so this is valid
            self.assertEquals(answer.as_text, reports_df[answer.question.identifier][0])
        self.assertEquals(reports_df['EA'][0], self.ea.name)
        for location in self.ea.locations.first().get_ancestors().exclude(id=Location.country().id):
            self.assertEquals(reports_df[location.type.name][0], location.name)

