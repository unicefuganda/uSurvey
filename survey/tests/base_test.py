import csv
from random import randint
from urllib import quote
from datetime import date

from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
import xlwt
from survey.models import LocationTypeDetails
from survey.models import Household
from survey.models import HouseholdHead


class BaseTest(TestCase):

    def assign_permission_to(self, user, permission_type='can_view_investigators'):
        some_group = Group.objects.create(name='some group that %s'% permission_type)
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename=permission_type, content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(user)
        return user

    def assert_not_allowed_when_batch_is_open(self, url, expected_redirect_url, expected_message):
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=expected_redirect_url, status_code=302, target_status_code=200, msg_prefix='')
        self.assertIn(expected_message, response.cookies['messages'].value)

    def assert_restricted_permission_for(self, url):
        self.client.logout()
        self.client.login(username='useless', password='I_Suck')
        response = self.client.get(url)
        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%quote(url), status_code=302, target_status_code=200, msg_prefix='')

    def assert_login_required(self, url):
        self.client.logout()
        response = self.client.get(url)
        self.assertRedirects(response, expected_url='/accounts/login/?next=%s'%quote(url), status_code=302, target_status_code=200, msg_prefix='')

    def assert_dictionary_equal(self, dict1, dict2): # needed as QuerySet objects can't be equated -- just to not override .equals
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
        for i in xrange(1, size+1):
            for j in xrange(size):
                sheet1.write(i, j, randint(0,100))
        book.save(filename)

    def generate_location_type_details(self, location, the_country):
        LocationTypeDetails.objects.get_or_create(country=the_country, location_type=location.type)
        if location.get_children().exists():
            self.generate_location_type_details(location.get_children()[0], the_country)

    def create_household_head(self, uid, investigator, survey=None):
        self.household = Household.objects.create(investigator=investigator, ea=investigator.ea,
                                                  uid=uid, survey=survey)
        return HouseholdHead.objects.create(household=self.household, surname="Name " + str(randint(1, 9999)),
                                            date_of_birth=date(1990, 2, 9))
