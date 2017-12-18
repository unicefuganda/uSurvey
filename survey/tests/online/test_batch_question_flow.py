import json
import re
import redis
from model_mommy import mommy
from django.core.cache import cache
from django.conf import settings
from copy import deepcopy
from django.test.client import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.forms import widgets
from django.template.loader import get_template
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from survey.models import *
from survey.online.views import respond
from survey.tests.base_test import BaseTest
from survey.forms.question_set import BatchForm
from survey.forms.answer import SurveyAllocationForm, AddMoreLoopForm
from survey.tests.models.survey_base_test import SurveyBaseTest


class OnlineFlowsTest(BaseTest):
    fixtures = ['enumeration_area', 'locations', 'location_types']

    def setUp(self):
        self.client = Client()
        self.survey = mommy.make(Survey)
        self.batch_data = {'name': 'test-batch', 'access_channels': [ODKAccess.choice_name(), ],
                           'survey': self.survey.id}
        self.questions_data = []
        # create a inline flows for this listing
        for answer_class in [NumericalAnswer, TextAnswer, DateAnswer, MultiChoiceAnswer]:
            self.questions_data.append({'text': 'text: %s' % answer_class.choice_name(),
                                        'answer_type': answer_class.choice_name(),
                                        'identifier': 'id_%s' % answer_class.choice_name().replace(' ', '_')})
        self.questions_data[-1]['options'] = ['Yes', 'No']
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client.login(username='demo12', password='demo12')

    def test_add_batch(self):
        show_batch_page_url = reverse('batch_index_page', args=(self.survey.pk, ))
        response = self.client.get(show_batch_page_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Batch.objects.count(), 0)
        create_batch_url = reverse('new_batch_page', args=(self.survey.pk, ))
        response = self.client.post(create_batch_url, data=self.batch_data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Batch.objects.count(), 1)

    def test_create_group(self):
        group_params = {'text': 'age 1', 'answer_type': NumericalAnswer.choice_name(), 'identifier': 'age'}
        # check if you can reach the show params to add one
        show_param_url = reverse('show_%s' % ParameterTemplate.resolve_tag())
        response = self.client.post(show_param_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(ParameterTemplate.objects.count(), 0)
        create_params_url = reverse('new_%s' % ParameterTemplate.resolve_tag())
        response = self.client.post(create_params_url, data=group_params)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(ParameterTemplate.objects.count(), 1)
        # check if grou
        group_params = {'text': 'Choose', 'answer_type': MultiChoiceAnswer.choice_name(), 'identifier': 'choice',
                        'options': ['Yes', 'No']}
        # check if you can reach the show params to add one
        response = self.client.post(create_params_url, data=group_params)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(ParameterTemplate.objects.count(), 2)
        show_groups_url = reverse('respondent_groups_page')
        response = self.client.get(show_groups_url)
        self.assertEquals(response.status_code, 302)    # only users with 'auth.can_view_household_groups' can access
        self.assign_permission_to(User.objects.create_user('user1', 'user@kant1.com', 'demo123'),
                                  'can_view_household_groups')
        client = Client()
        client.login(username='user1', password='demo123')
        response = client.get(show_groups_url)
        self.assertEquals(response.status_code, 200)
        create_group_url = reverse('new_respondent_groups_page')
        group_data = {'name': 'group1', 'description': 'etc',
                      'test_question': ParameterTemplate.objects.order_by('created').first().id,
                      'validation_test': 'between', 'min': 3, 'max': 5}
        response = client.post(create_group_url, data=group_data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(RespondentGroup.objects.count(), 1)
        group = RespondentGroup.objects.first()
        edit_group_url = reverse('respondent_groups_edit', args=(group.id, ))
        self.assertIn(edit_group_url, response.url)
        group_data = {'name': 'group1', 'description': 'etc', 'validation_test': 'equals',
                      'test_question': ParameterTemplate.objects.order_by('created').last().id,
                      'value': 1}
        response = client.post(edit_group_url, data=group_data)        #just post to same url
        self.assertEquals(RespondentGroup.objects.first().group_conditions.count(), 2)
        self.assertEquals(response.status_code, 302)
        self.assertIn(edit_group_url, response.url)

    def test_add_questions_to_batch(self):
        self.test_add_batch()
        self.test_create_group()
        batch = Batch.objects.first()
        group = RespondentGroup.objects.first()
        create_sq_url = reverse('new_qset_question_page', args=(batch.pk, ))
        i = 0
        question_data = self.questions_data
        question_data[1]['group'] = group.id
        question_data[3]['group'] = group.id
        for idx, data in enumerate(question_data):
            data['qset'] = batch.pk
            response = self.client.post(create_sq_url, data=data)
            self.assertEquals(len(batch.flow_questions), idx+1),
            question = batch.flow_questions[-1]
            self.assertEquals(question.text, data['text'])
            self.assertEquals(question.identifier, data['identifier'])
            self.assertEquals(question.answer_type, data['answer_type'])
            self.assertEquals(question.qset.pk, batch.pk)
            if 'group' in data:
                self.assertEquals(question.group.id, data['group'])
        # now check that the first batch question is parameter first.
        first_param = ParameterQuestion.objects.order_by('created').first().pk
        self.assertEquals(batch.g_first_question.pk, first_param)
        last_param = ParameterQuestion.objects.order_by('created').last()
        self.assertEquals(batch.all_questions[1].pk, last_param.pk)
        self.assertEquals(len(batch.all_questions), ParameterQuestion.objects.count() + BatchQuestion.objects.count())


class USSDFlowTest(SurveyBaseTest):

    def setUp(self):
        super(USSDFlowTest, self).setUp()
        self.ussd_access = USSDAccess.objects.create(interviewer=self.interviewer, user_identifier='312313800')
        self._create_ussd_group_questions()

    def test_ussd_flow_invalid_msisdn_gives_error_msg(self):
        ussd_url = reverse('ussd')
        data = {settings.USSD_MOBILE_NUMBER_FIELD: '',
                settings.USSD_MSG_FIELD: ''}
        response = self.client.get(ussd_url, data=data)
        self.assertEquals('Invalid mobile number', response.content)
        data = {settings.USSD_MOBILE_NUMBER_FIELD: '+254795466275',
                settings.USSD_MSG_FIELD: ''}
        response = self.client.get(ussd_url, data=data)
        self.assertEquals('Invalid mobile number for your region', response.content)

    def test_ussd_flow_with_valid_msisdn(self):
        ussd_url = reverse('ussd')
        data = {settings.USSD_MOBILE_NUMBER_FIELD: self.ussd_access.user_identifier,
                settings.USSD_MSG_FIELD: ''}
        response = self.client.get(ussd_url, data=data)
        # at this stage no open surveys yet even though there is survey allocation
        template = get_template('interviews/no-open-survey.html')
        self.assertIn(template.render({'access': self.ussd_access, 'display_format': 'text'}).strip(),
                      response.content.strip())
        # now open all locations
        country = Location.country()
        for location in country.get_children():
            self.qset.open_for_location(location)
        response = self.client.get(ussd_url, data=data)
        # check this form requires user to select EA
        self.assertIn(self.survey_allocation.allocation_ea.name.upper(), response.content.upper())
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(ussd_url, data=data)
        self.assertIn(self.qset.g_first_question.text.upper(), response.content.upper())     # numeric answer
        data[settings.USSD_MSG_FIELD] = 3
        response = self.client.get(ussd_url, data=data)
        all_questions = self.qset.all_questions
        self.assertIn(all_questions[1].text.upper(), response.content.upper())  # text answer

    def test_ussd_flow_no_uid(self):
        url = reverse('ussd')
        data = {'format': 'text'}
        request = RequestFactory().get(url, data=data)
        response = respond(request)
        self.assertEquals(response.status_code, 200)

    def test_flow_with_sampled_flow(self):
        listing_form = mommy.make(ListingTemplate)
        lquestion = mommy.make(Question, qset=listing_form,
                              answer_type=NumericalAnswer.choice_name(), text='numeric-sample')
        listing_form.start_question = lquestion
        listing_form.save()
        self.survey.has_sampling = True
        self.survey.listing_form = listing_form
        self.survey.sample_size = 2
        self.survey.random_sample_label = 'Facility-{{%s}}' % listing_form.all_questions[-1].identifier
        self.survey.save()
        self.qset.name = 'first-batch'
        self.qset.save()
        batch2 = mommy.make(Batch, survey=self.survey, name='a-new-batch')
        question = mommy.make(Question, qset=batch2,
                              answer_type=TextAnswer.choice_name(), text='text-batch-sample')
        # self._create_ussd_non_group_questions(listing_form)
        data = {settings.USSD_MOBILE_NUMBER_FIELD: self.ussd_access.user_identifier,
                settings.USSD_MSG_FIELD: ''}
        url = reverse('ussd')
        country = Location.country()
        # now open for batch2 locations
        for location in country.get_children():
            self.qset.open_for_location(location)       # open batches in locations
        for location in country.get_children():
            batch2.open_for_location(location)       # open batches in locations
        response = self.client.get(url, data=data)
        # confirm select ea
        self.assertIn(self.survey_allocation.allocation_ea.name.upper(), response.content.upper())
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(url, data=data)
        # for as long as sample size is not reached keep asking listing question
        self.assertIn('numeric-sample', response.content)
        data[settings.USSD_MSG_FIELD] = 17
        response = self.client.get(url, data=data)
        self.assertIn('Survey Completed', response.content)
        # any value should work now
        data[settings.USSD_MSG_FIELD] = '8ddhjsd6'
        response = self.client.get(url, data=data)
        # should return to home page
        self.assertIn('Welcome', response.content)
        # since sample size is two it should repeat listing at least twice. After the second,
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(url, data=data)
        data[settings.USSD_MSG_FIELD] = 25
        response = self.client.get(url, data=data)
        self.assertIn('Survey Completed', response.content)
        # any value should work now
        data[settings.USSD_MSG_FIELD] = '8ddau783ehj'
        # return to home page
        response = self.client.get(url, data=data)
        self.assertIn('select', response.content.lower())
        self.assertIn('ea', response.content.lower())
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(url, data=data)
        # at this point ask if user wants to continue listing or not
        self.assertIn('continue', response.content.lower())
        self.assertIn('listing', response.content.lower())
        self.assertIn('listing', response.context['answer_form'].render_extra_ussd_html().lower())
        self.assertIn('batch', response.context['answer_form'].render_extra_ussd_html().lower())
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(url, data=data)
        # if yes, confirm listing question is present
        self.assertIn('numeric-sample', response.content)
        data[settings.USSD_MSG_FIELD] = 29
        response = self.client.get(url, data=data)
        self.assertIn('Survey Completed', response.content)
        # any value should restart to welcome page
        data[settings.USSD_MSG_FIELD] = '8ddau783ehj'
        response = self.client.get(url, data=data)
        self.assertIn('select', response.content.lower())
        self.assertIn('ea', response.content.lower())
        # ea select and proceed to choose listing or batch
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(url, data=data)
        self.assertIn('continue', response.content.lower())
        self.assertIn('listing', response.content.lower())
        data[settings.USSD_MSG_FIELD] = 2           # choose to start batch
        response = self.client.get(url, data=data)
        sample_strings = re.findall('.+(Facility-[0-9]{2}).*', response.content)
        sample_base = ['Facility-%s' % answer.as_text for answer in lquestion.answer.all()]
        for sample in sample_strings:       # to start batch, you need to select randaom sample
            self.assertIn(sample, sample_base)
            self.assertIn(sample.lower(), response.context['answer_form'].render_extra_ussd_html().lower())
        data[settings.USSD_MSG_FIELD] = 2       # select second sample
        response = self.client.get(url, data=data)
        self.assertIn(self.qset.name, response.content)     # confirm second batch is returned
        self.assertIn(batch2.name, response.content)
        self.assertIn(self.qset.name, response.context['answer_form'].render_extra_ussd())
        self.assertIn(batch2.name, response.context['answer_form'].render_extra_ussd_html())
        data[settings.USSD_MSG_FIELD] = 2       # this should select qset.name since its second entry ordered by name
        response = self.client.get(url, data=data)
        all_questions = self.qset.all_questions
        self.assertIn(self.qset.g_first_question.text, response.content)
        self.assertIn(all_questions[0].text, response.content)      # confirm param question
        data[settings.USSD_MSG_FIELD] = 88
        response = self.client.get(url, data=data)
        data[settings.USSD_MSG_FIELD] = 23
        self.assertIn(all_questions[1].text, response.content)          # confirm  numeric
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[2].text, response.content)          # confirm text
        data[settings.USSD_MSG_FIELD] = 'something nice'
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[3].text, response.content)          # confirm multichoice
        data[settings.USSD_MSG_FIELD] = '2'         # basically select no
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[4].text, response.content)          # confirm auto
        response = self.client.get(url, data=data)
        self.assertIn('Survey Completed', response.content)

    def test_non_ussd_flows(self):
        qset = self.qset1
        country = Location.country()
        for location in country.get_children():
            qset.open_for_location(location)
        # just create batch with non-ussd questions
        dq = mommy.make(Question, qset=qset, text='date_answer-sdosod', answer_type=DateAnswer.choice_name())
        odkq = mommy.make(Question, qset=qset, text='odk_answer-0sd384s', answer_type=GeopointAnswer.choice_name())
        ikq = mommy.make(Question, qset=qset, text='image_answer-9923uhdisb', answer_type=ImageAnswer.choice_name())
        qset.start_question = dq
        qset.save()
        mommy.make(QuestionFlow, question=dq, next_question=odkq)
        mommy.make(QuestionFlow, question=odkq, next_question=ikq)
        url = reverse("test_qset_flow", args=(qset.id, ))
        data = dict()
        data['uid'] = self.access_channel.user_identifier
        self.client = Client()
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client.login(username='demo12', password='demo12')
        response = self.client.get(url)
        self.assertIn(dq.text, response.content)
        self.assertTrue(isinstance(response.context['answer_form'].fields['value'].widget, widgets.DateInput))
        response = self.client.get(url, data={'value': '21-07-2017'})
        self.assertIn(odkq.text, response.content)
        response = self.client.get(url, data={'value': '12 9 20 1'})
        self.assertIn(ikq.text, response.content)
        self.assertTrue(isinstance(response.context['answer_form'].fields['value'].widget, widgets.FileInput))
        # test go back
        response = self.client.get(url, data={'value': '', 'go-back': True})
        self.assertIn(odkq.text, response.content)
        self.assertTrue(isinstance(response.context['answer_form'].fields['value'].widget, widgets.TextInput))
        # answer again
        response = self.client.get(url, data={'value': '15 9 10 1'})
        self.assertIn(ikq.text, response.content)
        import os
        BASE_DIR = os.path.dirname(__file__)
        image_path = os.path.join(BASE_DIR, 'testimage.png')
        sfi = SimpleUploadedFile('sample_image.png', open(image_path).read(), content_type='image/png')
        response = self.client.post(url, {'value': sfi})
        self.assertEquals(response.status_code, 200)

    def test_flow_with_loop(self):
        all_questions = self.qset.all_questions
        # loops cannot start with param questions
        loop = mommy.make(QuestionLoop, loop_starter=all_questions[1], loop_ender=all_questions[3],
                          repeat_logic=QuestionLoop.FIXED_REPEATS)
        mommy.make(FixedLoopCount, value=2, loop=loop)
        # mommy.make(QuestionLoop, loop_starter=all_questions[3], loop_ender=all_questions[4],
        #            repeat_logic=QuestionLoop.PREVIOUS_QUESTION)

        qset = self.qset
        url = reverse("test_qset_flow", args=(qset.id,))
        data = dict()
        self.client = Client()
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client.login(username='demo12', password='demo12')
        data['uid'] = self.access_channel.user_identifier
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[0].text, response.content)
        data['value'] = 12
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[1].text, response.content)
        data['value'] = 4
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[2].text, response.content)
        data['value'] = 'hey man'
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[3].text, response.content)
        data['value'] = 2
        response = self.client.get(url, data=data)
        # at this point, we must return to first loop
        self.assertIn(all_questions[1].text, response.content)
        data['value'] = 18
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[2].text, response.content)
        data['value'] = 'hey boy'
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[3].text, response.content)
        data['value'] = 1
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[4].text, response.content)
        data['value'] = 17
        response = self.client.get(url, data=data)
        self.assertIn(response.context['template_file'], 'interviews/completed.html')

    def test_auto_answer_loop_flows(self):
        qset = self.qset1
        country = Location.country()
        for location in country.get_children():
            qset.open_for_location(location)
        # just create batch with non-ussd questions
        nq = mommy.make(Question, qset=qset, text='numeric_answer-9923uhdisb',
                        answer_type=NumericalAnswer.choice_name())
        aq = mommy.make(Question, qset=qset, text='auto_answer-sdosod', answer_type=AutoResponse.choice_name())
        tq = mommy.make(Question, qset=qset, text='text_answer-0sd384s', answer_type=TextAnswer.choice_name())
        tq2 = mommy.make(Question, qset=qset, text='text2_answer-99siusuddisb', answer_type=TextAnswer.choice_name())
        qset.start_question = nq
        qset.save()
        mommy.make(QuestionFlow, question=nq, next_question=aq)
        mommy.make(QuestionFlow, question=aq, next_question=tq)
        mommy.make(QuestionFlow, question=tq, next_question=tq2)
        all_questions = qset.all_questions
        loop = mommy.make(QuestionLoop, loop_starter=all_questions[1], loop_ender=all_questions[3],
                          repeat_logic=QuestionLoop.PREVIOUS_QUESTION)
        mommy.make(PreviousAnswerCount, value=all_questions[0], loop=loop)
        #url = reverse("test_qset_flow", args=(qset.id,))
        url = reverse('ussd')
        data = {settings.USSD_MOBILE_NUMBER_FIELD: self.ussd_access.user_identifier, }
        self.client = Client()
        raj = self.assign_permission_to(User.objects.create_user('demo12', 'demo12@kant.com', 'demo12'),
                                        'can_view_batches')
        self.client.login(username='demo12', password='demo12')
        # data['uid'] = self.access_channel.user_identifier
        response = self.client.get(url, data=data)
        self.assertIn(self.survey_allocation.allocation_ea.name.upper(), response.content.upper())
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[0].text, response.content)
        data[settings.USSD_MSG_FIELD] = 2
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[1].text, response.content)
        data[settings.USSD_MSG_FIELD] = 4
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[2].text, response.content)
        data[settings.USSD_MSG_FIELD] = 'Somethin nice'
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[3].text, response.content)
        data[settings.USSD_MSG_FIELD] = 'Cool man'
        response = self.client.get(url, data=data)
        # should repead the loop 2 times as per first quest
        self.assertIn(all_questions[1].text, response.content)
        data[settings.USSD_MSG_FIELD] = 34
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[2].text, response.content)
        data[settings.USSD_MSG_FIELD] = 'Somethin nice2'
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[3].text, response.content)
        data[settings.USSD_MSG_FIELD] = 'Cool man2'
        response = self.client.get(url, data=data)
        self.assertIn(response.context['template_file'],'interviews/completed.html')

    def test_restart_flow(self):
        access = self.access_channel
        url = reverse('ussd')
        country = Location.country()
        # now open for batch2 locations
        for location in country.get_children():
            self.qset.open_for_location(location)  # open batches in locations
        data = {settings.USSD_MOBILE_NUMBER_FIELD: '312313801', settings.USSD_MSG_FIELD: ''}
        response = self.client.get(url, data=data)
        self.assertIn('No such interviewer', response.content)
        data[settings.USSD_MOBILE_NUMBER_FIELD] = self.ussd_access.user_identifier
        response = self.client.get(url, data=data)
        all_questions = self.qset.all_questions
        # confirm select ea
        self.assertIn(self.survey_allocation.allocation_ea.name.upper(), response.content.upper())
        self.assertIn(self.survey_allocation.allocation_ea.name.upper(),
                      response.context['answer_form'].render_extra_ussd_html().upper())
        self.assertIn(self.survey_allocation.allocation_ea.name.upper(),
                      response.context['answer_form'].render_extra_ussd().upper())
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(url, data=data)
        # ea selected. answer question 1
        self.assertIn(all_questions[0].text, response.content)
        data[settings.USSD_MSG_FIELD] = 17
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[1].text, response.content)
        data[settings.USSD_MSG_FIELD] = 27
        response = self.client.get(url, data=data)
        self.assertIn(all_questions[2].text, response.content)
        refresh_url = reverse('refresh_data_entry', args=(self.ussd_access.id, ))
        self.client.get(refresh_url, data=data)
        del data[settings.USSD_MSG_FIELD]
        response = self.client.get(url, data=data)
        self.assertIn(self.survey_allocation.allocation_ea.name.upper(), response.content.upper())
        data[settings.USSD_MSG_FIELD] = 1
        response = self.client.get(url, data=data)
        # ea selected. answer question 1
        self.assertIn(all_questions[0].text, response.content)


class AnswerFormExtra(SurveyBaseTest):

    def setUp(self):
        super(AnswerFormExtra, self).setUp()
        self.ussd_access = USSDAccess.objects.create(interviewer=self.interviewer, user_identifier='312313800')

    def test_loop_answer_form(self):
        url = reverse('ussd')
        request = RequestFactory().get(url)
        request.user = User.objects.create_user('demo12', 'demo12@kant.com', 'demo12')
        answer_form = AddMoreLoopForm(request, self.ussd_access)
        self.assertTrue(isinstance(answer_form.fields['value'].widget, forms.NumberInput))
        for choice in AddMoreLoopForm.CHOICES:
            self.assertIn('%s: %s' % choice, answer_form.render_extra_ussd())
            self.assertIn('%s: %s' % choice, answer_form.render_extra_ussd_html())



























