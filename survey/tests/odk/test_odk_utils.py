__author__ = 'antsmc2'
import time
from django.core.files.uploadedfile import SimpleUploadedFile
from lxml import etree
import python_digest
from model_mommy import mommy
import random
from hashlib import md5
from django.test import TestCase
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.auth.models import User
from survey.models import (InterviewerAccess, ODKAccess, USSDAccess, Interview, Interviewer, QuestionSetChannel,
                           EnumerationArea, Survey, SurveyAllocation, Question, QuestionSet, Batch, BatchQuestion,
                           QuestionOption, ODKSubmission)
from survey.forms.question import get_question_form
# import all question types
from survey.models import (Answer, NumericalAnswer, TextAnswer, MultiChoiceAnswer, MultiSelectAnswer, GeopointAnswer,
                           ImageAnswer, AudioAnswer, VideoAnswer, DateAnswer, AutoResponse)
from survey.tests.models.survey_base_test import SurveyBaseTest


class ODKTest(SurveyBaseTest):

    def setUp(self):
        super(ODKTest, self).setUp()
        self.odk_user = ODKAccess.objects.create(interviewer=self.interviewer, user_identifier='ants',
                                                 odk_token='antsman')

    def _save_ussd_compatible_questions(self):
        self._create_ussd_non_group_questions()

    def _make_odk_request(self, url=reverse('odk_survey_forms_list'), data=None, content_type=None, raw=False):
        username = self.odk_user.user_identifier
        password = self.odk_user.odk_token
        auth_headers = {}
        if content_type:
            auth_headers['content_type'] = content_type
        if data is None:
            # first do digest challeng
            response = self.client.get(url)
            self.assertEquals(response.status_code, 401)
            digest_challenge = response.get('www-authenticate')
            auth_headers['HTTP_AUTHORIZATION'] = self._get_digest_header(username, password, 'get',
                                                                         url, digest_challenge)
            return self.client.get(url, **auth_headers)
        else:
            response = self.client.post(url)
            self.assertEquals(response.status_code, 401)
            digest_challenge = response.get('www-authenticate')
            auth_headers['HTTP_AUTHORIZATION'] = self._get_digest_header(username, password, 'post',
                                                                         url, digest_challenge)
            if raw:
                return self.client.post(url, data, **auth_headers)
            else:
                return self.client.post(url, data=data, **auth_headers)

    def _get_digest_header(self, username, password, method, uri, digest_challenge):
        return python_digest.build_authorization_request(
            username,
            method.upper(),
            uri,
            1,  # nonce_count
            digest_challenge=digest_challenge,
            password=password
        )

    def test_form_list_throws_no_error(self):
        response = self._make_odk_request()
        self.assertEquals(response.status_code, 200)

    def test_no_xform_without_opening_batch(self):
        response = self._make_odk_request()
        self.assertEquals(response.status_code, 200)
        qset = QuestionSet.objects.first()
        path = '<formID>%s</formID>' % qset.pk
        self.assertNotIn(path, response.content)

    def test_xform_with_opening_batch(self):
        batch = QuestionSet.get(id=self.qset.id)
        batch.open_for_location(self.ea.locations.first())
        response = self._make_odk_request()
        self.assertEquals(response.status_code, 200)
        path = '<formID>%s</formID>' % batch.pk
        self.assertIn(path, response.content)

    def test_batch_without_questions_has_empty_questions_section_in_xform(self):
        url = reverse('download_odk_batch_form', args=(self.qset.id, ))
        response = self._make_odk_request(url=url)
        self.assertEquals(response.status_code, 200)
        # at least some reference representation would be there is it's been referenec some how
        self.assertNotIn('ref="/qset/qset%s/questions/surveyQuestions' % self.qset.id, response.content)

    def test_select_batch_odk_question(self):
        self._save_ussd_compatible_questions()
        url = reverse('download_odk_batch_form', args=(self.qset.id, ))
        response = self._make_odk_request(url=url)
        self.assertEquals(response.status_code, 200)
        survey_tree = etree.fromstring(response.content)
        path = '/qset/qset%s/questions/surveyQuestions/q%s' % (self.qset.id, self.qset.questions.first().id)
        self.assertIn(path, response.content)

    def _get_completed_xform(self, answer1, answer2, answer3, answer4):
        completed = b'''<qset id="%(qset)s" >
                         <meta>
                            <instanceID>%(instance_id)s</instanceID>
                            <instanceName>%(instance_id)s-Name</instanceName>
                        <creationDate />
                        <locked />
                         </meta>
                         <submissions>
                             <id />
                             <dates>
                                 <lastModified />
                             </dates>
                         </submissions>
                           <surveyAllocation>%(survey_allocation)s</surveyAllocation>
                           <qset1>
                            <questions>
                                <groupQuestions></groupQuestions>
                                <surveyQuestions>
                                    <q1>%(answer1)s</q1><q2>%(answer2)s</q2><q3>%(answer3)s</q3><q4>%(answer4)s</q4>
                                </surveyQuestions>
                            </questions>
                           </qset1>
                       </qset>
                       '''
        context = {'qset': self.qset.id, 'instance_id': random.randint(0, 1000),
                   'survey_allocation': self.survey_allocation.allocation_ea.name.encode('utf8'),
                   'answer1': answer1, 'answer2': answer2, 'answer3': answer3, 'answer4': answer4}
        return completed % context

    def test_submit_xform(self):
        self._save_ussd_compatible_questions()
        xml = self._get_completed_xform('2', 'James', 'Y', '1')
        f = SimpleUploadedFile("surveyfile.xml", xml)
        url = reverse('odk_submit_forms')
        response = self._make_odk_request(url=url, data={'xml_submission_file': f}, raw=True)
        self.assertTrue( 300 > response.status_code and response.status_code >= 200)
        self.assertEquals(ODKSubmission.objects.count(), 1)
        # not confirm that 4 responses were given
        self.assertEquals(Answer.objects.count(), 4)
        # now test the instances listpage
        url = reverse('odk_submission_list')
        # check all the if the
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_aggregates')
        client = Client()
        client.login(username='Rajni', password='I_Rock')
        response = client.get(url)
        templates = [template.name for template in response.templates]
        self.assertIn('odk/submission_list.html', templates)
        self.assertEquals(response.context['submissions'].count(), 1)
        # check instances list on ODK
        url = reverse('instances_form_list')
        response = self._make_odk_request(url=url)
        templates = [template.name for template in response.templates]
        self.assertIn("odk/instances_xformsList.xml", templates)
        self.assertEquals(response.context['submissions'].count(), 1)
        self.assertEquals(response.context['submissions'].filter(status=ODKSubmission.COMPLETED).count(), 1)
        submission = response.context['submissions'].first()
        # try to download the previously submitted form
        url = reverse('download_odk_submission', args=(submission.pk, ))
        response = self._make_odk_request(url=url)
        self.assertTrue( 300 > response.status_code and response.status_code >= 200)
        self.assertEquals(submission.xml.strip(), response.content.strip())
        tree = etree.fromstring(submission.xml)
        dates_nodes = tree.xpath('//qset/submissions/dates/lastModified')
        # this field is only included when updating instances
        self.assertEquals(len([d.text for d in dates_nodes if d.text]), 1)
        self.assertEquals(tree.xpath('//qset/submissions/id')[0].text, str(submission.id))
        # now submit modified form
        f = SimpleUploadedFile("surveyfile.xml", submission.xml.encode('utf8'))
        url = reverse('odk_submit_forms')
        response = self._make_odk_request(url=url, data={'xml_submission_file': f}, raw=True)
        self.assertTrue(300 > response.status_code and response.status_code >= 200)
        self.assertEquals(ODKSubmission.objects.count(), 1)
        self.assertEquals(Answer.objects.count(), 4)        # note: update only doesn't increase answer or subs count
        submission = ODKSubmission.objects.order_by('created').last()
        tree = etree.fromstring(submission.xml)
        # this field is only included when updating instances
        self.assertEquals(tree.xpath('//qset/submissions/id')[0].text, str(submission.id))








