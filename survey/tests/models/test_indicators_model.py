from model_mommy import mommy
import json
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse
from survey.models import *
from survey.tests.models.survey_base_test import SurveyBaseTest


class IndicatorTest(SurveyBaseTest):

    def _prep_answers(self, ea=None, num_subtract=0):
        if ea is None:
            ea = self.ea
        answers = []
        n_quest = Question.objects.get(answer_type=NumericalAnswer.choice_name())
        t_quest = Question.objects.get(answer_type=TextAnswer.choice_name())
        m_quest = Question.objects.get(answer_type=MultiChoiceAnswer.choice_name())
        ncount = NumericalAnswer.objects.count()
        mcount = MultiChoiceAnswer.objects.count()
        tcount = TextAnswer.objects.count()
        # first is numeric, then text, then multichioice
        answers = [{n_quest.id: 1-num_subtract, t_quest.id: 'Hey Man', m_quest.id: 'Y'},
                   {n_quest.id: 5-num_subtract, t_quest.id: 'Our Hey Boy', m_quest.id: 'Y'},
                   {n_quest.id: 27-num_subtract, t_quest.id: 'Hey Girl!', m_quest.id: 'N'},
                   {n_quest.id: 12-num_subtract, t_quest.id: 'Hey Raster!', m_quest.id: 'N'},
                   {n_quest.id: 19-num_subtract, t_quest.id: 'This bad boy'}
                   ]
        question_map = {n_quest.id: n_quest, t_quest.id: t_quest, m_quest.id: m_quest}
        interview = self.interview
        interviews = Interview.save_answers(self.qset, self.survey, ea,
                                            self.access_channel, question_map, answers)
        # confirm that 11 answers has been created
        self.assertEquals(NumericalAnswer.objects.count(), ncount + 5)
        self.assertEquals(TextAnswer.objects.count(), tcount + 5)
        self.assertEquals(MultiChoiceAnswer.objects.count(), mcount + 4)
        return Interview.objects.filter(id__in=[i.id for i in interviews])

    def test_indicator_calculations(self):
        self._create_test_non_group_questions(self.qset)
        n_quest = Question.objects.get(answer_type=NumericalAnswer.choice_name())
        t_quest = Question.objects.get(answer_type=TextAnswer.choice_name())
        # create answers according to present ea
        self._prep_answers()        # creates answers with 3 numeric above 5, 4 answers with hey
        interviewer2 = mommy.make(Interviewer)
        ea2 = EnumerationArea.objects.exclude(locations__parent=self.ea.locations.first().parent).first()
        survey_allocation2 = mommy.make(SurveyAllocation, interviewer=interviewer2,
                                        survey=self.survey, allocation_ea=ea2)
        self._prep_answers(ea=ea2, num_subtract=10)     # creates answers with 2 above 5, 4 answers with hey
        indicator = mommy.make(Indicator, question_set=self.qset, survey=self.survey)
        self.assertEquals(str(indicator), indicator.name)
        indicator_variable1 = mommy.make(IndicatorVariable, indicator=indicator)
        criteria = mommy.make(IndicatorVariableCriteria,  variable=indicator_variable1,
                              test_question=n_quest, validation_test='greater_than')
        mommy.make(IndicatorCriteriaTestArgument, criteria=criteria, position=1, param=5)
        indicator_variable2 = mommy.make(IndicatorVariable, indicator=indicator)
        criteria = mommy.make(IndicatorVariableCriteria,  variable=indicator_variable2,
                              test_question=t_quest, validation_test='contains')
        mommy.make(IndicatorCriteriaTestArgument, criteria=criteria, position=1, param='Hey')
        indicator.formulae = '{{%s}}/{{%s}}' % (indicator_variable1.name, indicator_variable2.name)
        indicator.save()
        df = indicator.get_data(self.ea.locations.first().parent)
        # remember, only 3 are about 5 in this ea. 4 interviews with hey word
        self.assertEquals(float(df[Indicator.REPORT_FIELD_NAME]), 3.0/4.0)
        df = indicator.get_data(ea2.locations.first().parent)
        # remember, only 2 are about 5 in this ea, 4 interviews with hey word
        self.assertEquals(float(df[Indicator.REPORT_FIELD_NAME]), 2.0/4.0)
        # 4 text questions, from each location, 5 questions from both locations
        country_report = indicator.country_wide_report()
        self.assertEquals(country_report[indicator_variable1.name], 5.0)
        self.assertEquals(country_report[indicator_variable2.name], 8.0)
        self.assertEquals(country_report[Indicator.REPORT_FIELD_NAME],
                          round(float(country_report[indicator_variable1.name]) /
                                float(country_report[indicator_variable2.name]),
                                Indicator.DECIMAL_PLACES))
        # sneek test, check if get indicator views is returning correct json
        url = reverse('survey_indicators')
        User.objects.create_user(username='useless', email='demo4@kant.com', password='I_Suck')
        self.raj = self.assign_permission_to(User.objects.create_user('demo4', 'demo4@kant.com', 'demo4'),
                                             'can_view_aggregates')
        self.client.login(username='demo4', password='demo4')
        response = self.client.get(url)
        self.assertFalse(json.loads(response.content))      # should be empty no indicator has display on dashboard
        indicator.display_on_dashboard = True
        indicator.save()
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEquals(len(data.keys()), 1)      # only one indicator
        country = Location.country()
        for location in country.get_children():
            self.assertIn(location.name.upper(), data[indicator.name])




