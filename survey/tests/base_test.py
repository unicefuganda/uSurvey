import csv
import redis
from random import randint
from urllib import quote
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test.utils import setup_test_environment
import xlwt
from model_mommy import mommy
from survey.models import Question
from survey.models import Batch, QuestionModule
from survey.models import AnswerAccessDefinition
from mock import patch
import datetime
from django.core.urlresolvers import reverse


class Base(TestCase):

    @classmethod
    def setUpTestData(cls):
        super(Base, cls).setUpTestData()
        setup_test_environment()
        AnswerAccessDefinition.reload_answer_categories()

    def tearDown(self):
        for i in range(16):
            store = redis.Redis(db=i)
            for key in store.keys():
                store.delete(key)

    def mock_date_today(self, target, real_date_class=datetime.date):
        class DateSubclassMeta(type):

            @classmethod
            def __instancecheck__(mcs, obj):
                return isinstance(obj, real_date_class)

        class BaseMockedDate(real_date_class):

            @classmethod
            def today(cls):
                return target

        # Python2 & Python3 compatible metaclass
        MockedDate = DateSubclassMeta('date', (BaseMockedDate,), {})

        return patch.object(datetime, 'date', MockedDate)


class BaseTest(Base):

    def assign_permission_to(
            self,
            user,
            permission_type='can_view_investigators'):
        some_group, created = Group.objects.get_or_create(name='some group that %s' % permission_type)
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename=permission_type, content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(user)
        return user

    def assert_not_allowed_when_batch_is_open(
            self, url, expected_redirect_url, expected_message):
        response = self.client.get(url)
        self.assertRedirects(
            response,
            expected_url=expected_redirect_url,
            status_code=302,
            target_status_code=200,
            msg_prefix='')
        self.assertIn(expected_message, response.cookies['messages'].value)

    def assert_restricted_permission_for(self, url, required_permission=None):
        self.client.logout()
        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)
        self.assertRedirects(
            response,
            expected_url='%s?next=%s' %
            (reverse('login_page'),
             quote(url)),
            status_code=302,
            target_status_code=200,
            msg_prefix='')
        if required_permission:
            self.client.logout()
            user = self.assign_permission_to(User.objects.create_user('test2', 'demo12@b.com', 'demo12'),
                                             'can_view_batches')
            self.client.login(username='test2', password='demo12')
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)

    def assert_login_required(self, url):
        self.client.logout()
        response = self.client.get(url)
        self.assertRedirects(
            response,
            expected_url='%s?next=%s' % (
                reverse('login_page'),quote(url)),
            status_code=302,
            target_status_code=200,
            msg_prefix='')

    # needed as QuerySet objects can't be equated -- just to not override
    # .equals
    def assert_dictionary_equal(self, dict1, dict2):
        self.assertEquals(len(dict1), len(dict2))
        dict2_keys = dict2.keys()
        for key in dict1.keys():
            self.assertIn(key, dict2_keys)
            for index in range(len(dict1[key])):
                self.assertEquals(dict1[key][index], dict2[key][index])

    def write_to_csv(self, mode, data, csvfilename='test.csv'):
        with open(csvfilename, mode) as fp:
            file = csv.writer(fp, delimiter=',')
            file.writerows(data)
            fp.close()

    def generate_non_csv_file(self, filename):
        book = xlwt.Workbook()
        sheet1 = book.add_sheet("Sheet 1")
        sheet1.write(0, 0, "RegionName")
        sheet1.write(0, 1, "DistrictName")
        sheet1.write(0, 2, "CountyName")
        size = 3
        for i in xrange(1, size + 1):
            for j in xrange(size):
                sheet1.write(i, j, randint(0, 100))
        book.save(filename)

    def assert_object_does_not_exist(self, url, message):
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)
        self.assertIn(message, response.cookies['messages'].value)
