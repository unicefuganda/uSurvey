import datetime
import json
import ast
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.test import Client
from survey.models.locations import *
from survey.models import *
from model_mommy import mommy
from survey.tests.base_test import BaseTest
from survey.views.survey_completion import is_valid
from django.core.urlresolvers import reverse

class TestSurveyCompletion(BaseTest):

    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.assign_permission_to(raj, 'can_view_aggregates')
        self.assign_permission_to(raj, 'view_completed_survey')
        self.client.login(username='Rajni', password='I_Rock')
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.region = LocationType.objects.create(
            name='Region', parent=self.country, slug='region')
        self.city = LocationType.objects.create(
            name='City', parent=self.region, slug='city')
        self.parish = LocationType.objects.create(
            name='Parish', parent=self.city, slug='parish')
        self.survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        self.africa = Location.objects.create(name='Africa', type=self.country)
        self.uganda = Location.objects.create(
            name='Uganda', type=self.region, parent=self.africa)
        self.abim = Location.objects.create(
            name='Abim', parent=self.uganda, type=self.city)
        self.kampala = Location.objects.create(
            name='Kampala', parent=self.uganda, type=self.city)
        self.bukoto = Location.objects.create(
            name='Kampala City', parent=self.kampala, type=self.parish)
        self.kampala_ea = EnumerationArea.objects.create(name="EA2")
        self.kampala_ea.locations.add(self.kampala)
        self.abim_ea = EnumerationArea.objects.create(name="ABIM EA")
        self.abim_ea.locations.add(self.abim)
        self.city_ea = EnumerationArea.objects.create(name="CITY EA")
        self.city_ea.locations.add(self.bukoto)
        self.ea = EnumerationArea.objects.create(name="BUBEMBE", code="11-BUBEMBE")
        self.investigator_1 = Interviewer.objects.create(name="Investigator",
                                                         ea=self.kampala_ea,
                                                         gender='1', level_of_education='Primary',
                                                         language='Eglish', weights=0)
        self.investigator_2 = Interviewer.objects.create(name="Investigator",
                                                         ea=self.city_ea,
                                                         gender='1', level_of_education='Primary',
                                                         language='Eglish', weights=0)
        self.batch = Batch.objects.create(
            order=1, name='somebatch', survey=self.survey)


    def test_validates_when_location_is_present_in_parameters_and_parameters_contains_batch_key(self):
        self.assertTrue(is_valid({'location': '', 'batch': '1'}))
        self.assertTrue(is_valid({'location': '2', 'batch': '1', 'ea': '1'}))
        self.assertTrue(is_valid({'location': '2', 'batch': '1', 'ea': ''}))

    def test_show_retrieves_high_level_completion_rates_if_no_location_is_provided(self):
        data = {'location': '',
                'batch': str(self.batch.pk),
                'survey': self.survey.id,
                'ea': ''}
        response = self.client.post('/surveys/completion/', data=data)
        self.assertIsNotNone(response.context['request'])

    def test_knows_to_retrieve_completion_for_locations_that_have_no_tree_parent_if_country_type_does_not_exist(self):
        LocationType.objects.filter(name__iexact='country').delete()
        location_with_no_parent = Location.objects.create(
            name='Unganda1', type=self.country)
        another_location_with_no_parent = Location.objects.create(
            name='Unganda12', type=self.country)
        form_data = {'survey': self.batch.survey.id, 'location': location_with_no_parent.id, 'batch': str(
            self.batch.pk), 'ea': self.kampala_ea.id}
        response = self.client.post('/surveys/completion/', data=form_data)
        self.assertIsNotNone(response.context['request'])

    def test_survey_completion(self):
        listing_form = ListingTemplate.objects.create(name='scomp1', description='desc1')
        kwargs = {'name': 'survey9scl', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        investigator = Interviewer.objects.create(name="InvestigatorViewdata1",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')

        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer = investigator,
            survey = survey_obj,
            allocation_ea = self.ea,
            status = 1

            )
        url = reverse('survey_completion_json', kwargs={"survey_id" : survey_obj.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.getvalue())
        location_name = self.uganda.name.upper()
        self.assertEqual(result[location_name]['total_eas'], 1)
        self.assertEqual(result[location_name]['active_eas'], 0)

    def test_survey_json_summary(self):
        listing_form = ListingTemplate.objects.create(name='scomp123', description='desc1')
        kwargs = {'name': 'survey9sclq11', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        investigator = Interviewer.objects.create(name="InvestigatorViewdata1",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')

        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer = investigator,
            survey = survey_obj,
            allocation_ea = self.ea,
            status = 1

            )
        url = reverse('survey_json_summary')
        url = url + "?survey=%s"%survey_obj.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.getvalue())
        
        url = reverse('survey_json_summary')
        url = url + "?survey=0000701"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_survey_indicators(self):
        listing_form = ListingTemplate.objects.create(name='scomp1333', description='desc1')
        kwargs = {'name': 'aasurvey9scl11qa', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(order=1, name="aaaBatch A1s22222", survey=survey_obj)
        qset = QuestionSet.get(pk=batch_obj.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        investigator = Interviewer.objects.create(name="InvestigatorViewdata1",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')

        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer = investigator,
            survey = survey_obj,
            allocation_ea = self.ea,
            status = 1

            )
        indicator_obj = Indicator.objects.create(name="indicator name 13ff34411", description="demo4 indicator 1",
                                               question_set=qset,
                                                survey=survey_obj)
        url = reverse('survey_indicators')
        url = url + "?survey=%s"%survey_obj.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        


    # def test_survey_parameters(self):
    #     listing_form = ListingTemplate.objects.create(name='scomp1333', description='desc1')
    #     kwargs = {'name': 'survey9scl11q', 'description': 'survey description demo12',
    #                       'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
    #     survey_obj = Survey.objects.create(**kwargs)
    #     batch_obj = Batch.objects.create(order=1, name="Batch A1s22222", survey=survey_obj)
    #     qset = QuestionSet.get(pk=batch_obj.id)
    #     question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
    #     investigator = Interviewer.objects.create(name="InvestigatorViewdata1",
    #                                                    ea=self.ea,
    #                                                    gender='1', level_of_education='Primary',
    #                                                    language='Eglish', weights=0,date_of_birth='1987-01-01')

    #     surveyAllocation_obj = SurveyAllocation.objects.create(
    #         interviewer = investigator,
    #         survey = survey_obj,
    #         allocation_ea = self.ea,
    #         status = 1

    #         )
    #     indicator_obj = Indicator.objects.create(name="indicator name 13ff3", description="demo4 indicator 1",
    #                                            question_set=qset,
    #                                             survey=survey_obj)
    #     url = reverse('survey_parameters')
    #     url = url + "?indicator=%s"%indicator_obj.id
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)

    #     url = reverse('survey_parameters')
    #     url = url + "?indicator=990033333"
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 404)

    def test_show_interviewer_completion_summary(self):
        listing_form = ListingTemplate.objects.create(name='scomp133329', description='desc1')
        kwargs = {'name': 'survey9scl11qqooo', 'description': 'survey description demo12',
                          'has_sampling': True, 'sample_size': 10,'listing_form_id':listing_form.id}
        survey_obj = Survey.objects.create(**kwargs)
        batch_obj = Batch.objects.create(order=1, name="Batch9dd A1s22222", survey=survey_obj)
        qset = QuestionSet.get(pk=batch_obj.id)
        question1 = mommy.make(Question, qset=qset, answer_type=NumericalAnswer.choice_name())
        investigator = Interviewer.objects.create(name="InvestigatorViewdata1",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0,date_of_birth='1987-01-01')

        surveyAllocation_obj = SurveyAllocation.objects.create(
            interviewer = investigator,
            survey = survey_obj,
            allocation_ea = self.ea,
            status = 1

            )
        indicator_obj = Indicator.objects.create(name="indicator name 13ff3", description="demo4 indicator 1",
                                               question_set=qset,
                                                survey=survey_obj)
        url = reverse('show_interviewer_completion_summary')
        url = url + "?q=%s"%(investigator.name)
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])
        #templates = [template.name for template in response.templates]
        #self.assertIn('aggregates/interviewers_summary.html', templates)
        
        # url = reverse('show_interviewer_completion_summary')
        # url = url + "?status=%s"%(ast.literal_eval(''))
        # self.assertIn(response.status_code, [200, 302])
        # templates = [template.name for template in response.templates]
        # self.assertIn('aggregates/interviewers_summary.html', templates)
        