# -*- coding: utf-8 -*-
from lettuce.django import django_url
from random import randint
from time import sleep
from rapidsms.contrib.locations.models import Location
from survey.models import Investigator
from survey.investigator_configs import *
from rapidsms.contrib.locations.models import *
from rapidsms.backends.database.models import BackendMessage


class PageObject(object):
    def __init__(self, browser):
        self.browser = browser

    def visit(self):
        self.browser.visit(django_url(self.url))

    def random_text(self, text):
        return text + str(randint(1, 999))

    def fill(self, name, value):
        self.browser.fill(name, value)

    def is_text_present(self, text):
        assert self.browser.is_text_present(text)

    def is_disabled(self, element_id):
        try:
            self.browser.find_by_css('#%s[disabled]' % element_id).first
            return True
        except Exception, e:
            return False

    def fill_in_with_js(self, jquery_id, object_id):
        script = '%s.val(%s).change(); %s.trigger("liszt:updated").chosen().change()' % (
        jquery_id, object_id, jquery_id)
        self.browser.execute_script(script)
        sleep(2)

    def submit(self):
        self.browser.find_by_css("form button").first.click()

    def see_logout_link(self):
        assert self.browser.find_link_by_text('logout')

    def see_the_about_link(self):
        assert self.browser.find_link_by_text('About')

    def click_the_about_link(self):
        self.browser.click_link_by_text('About')

    def check_anonymous_user_allowed_tabs(self):
        assert self.browser.find_link_by_text('About')
        assert self.browser.find_link_by_text('mMICS')
        assert self.browser.find_link_by_text('login')

    def check_data_entry_allowed_tabs(self):
        assert self.browser.find_link_by_text('About')
        assert self.browser.find_link_by_text('mMICS')

        assert self.browser.find_link_by_text('Households')
        assert self.browser.find_link_by_text('Investigators')

    def check_researcher_allowed_tabs(self):
        self.check_data_entry_allowed_tabs()
        assert self.browser.find_link_by_text('Batches')
        assert self.browser.find_link_by_text('Aggregates')

    def check_all_tabs(self):
        self.check_researcher_allowed_tabs()
        assert self.browser.find_link_by_text('Users')

    def check_researcher_not_allowed_tabs(self):
        assert not self.browser.find_link_by_text('Users')

    def check_data_entry_not_allowed_tabs(self):
        self.check_researcher_not_allowed_tabs()
        assert not self.browser.find_link_by_text('Aggregates')
        assert not self.browser.find_link_by_text('Batches')

    def check_anonymous_user_not_allowed_tabs(self):
        self.check_data_entry_not_allowed_tabs()
        assert not self.browser.find_link_by_text('Investigators')
        assert not self.browser.find_link_by_text('Households')

    def check_notify_investigators_drop_down_is_not_present(self):
        self.browser.click_link_by_text('Investigators')
        assert not self.browser.find_link_by_text('Notify Investigators')

    def choose_radio(self, name, value):
        js = "$('input:radio[name=%s][value=%s]').prop('checked', true).change()" % (name, value)
        self.browser.execute_script(js)


class NewInvestigatorPage(PageObject):
    url = "/investigators/new"

    def valid_page(self):
        fields = ['name', 'mobile_number', 'confirm_mobile_number', 'male', 'age', 'backend']
        for field in fields:
            assert self.browser.is_element_present_by_name(field)
        assert self.browser.find_by_css("span.add-on")[0].text == COUNTRY_PHONE_CODE

    def get_investigator_values(self):
        return self.values

    def fill_valid_values(self):
        self.browser.find_by_id("location-value").value = Location.objects.create(name="Uganda").id
        self.values = {
            'name': self.random_text('Investigator Name'),
            'mobile_number': "987654321",
            'confirm_mobile_number': "987654321",
            'male': 't',
            'age': '25',
            'level_of_education': 'Primary',
            'language': 'Luo',
        }
        self.browser.fill_form(self.values)
        kampala = Location.objects.get(name="Kampala")
        kampala_county = Location.objects.get(name="Kampala County")
        script = '$("#location-district").val(%s);$("#location-district").trigger("liszt:updated").chosen().change()' % kampala.id
        self.browser.execute_script(script)
        sleep(3)
        script = '$("#location-county").val(%s);$("#location-county").trigger("liszt:updated").chosen().change()' % kampala_county.id
        self.browser.execute_script(script)

    def submit(self):
        self.browser.find_by_css("form button").first.click()


class InvestigatorsListPage(PageObject):
    url = '/investigators/'

    def validate_fields(self):
        assert self.browser.is_text_present('Investigators List')
        assert self.browser.is_text_present('Name')
        assert self.browser.is_text_present('Mobile Number')
        assert self.browser.is_text_present('Action')

    def validate_pagination(self):
        self.browser.click_link_by_text("2")

    def validate_presence_of_investigator(self, values):
        assert self.browser.is_text_present(values['name'])
        assert self.browser.is_text_present(values['mobile_number'])

    def no_registered_invesitgators(self):
        assert self.browser.is_text_present("There are no investigators currently registered for this location.")

    def visit_investigator(self, investigator):
        self.browser.click_link_by_text(investigator.name)

    def click_actions_button(self):
        self.browser.find_by_css('#action_caret').first.click()

    def click_edit_button(self):
        self.browser.click_link_by_text(' Edit')

class FilteredInvestigatorsListPage(InvestigatorsListPage):
    def __init__(self, browser, location_id):
        self.browser = browser
        self.url = '/investigators/?location=' + str(location_id)

    def no_registered_invesitgators(self):
        assert self.browser.is_text_present("There are no investigators currently registered for this county.")


class NewHouseholdPage(PageObject):
    url = "/households/new"

    def valid_page(self):
        fields = ['investigator', 'surname', 'first_name', 'male', 'age', 'occupation',
                  'level_of_education', 'resident_since_month', 'resident_since_year']
        fields += ['number_of_males', 'number_of_females', 'size']
        fields += ['has_children', 'has_children_below_5', 'aged_between_5_12_years', 'aged_between_13_17_years',
                   'aged_between_0_5_months',
                   'aged_between_6_11_months', 'aged_between_12_23_months', 'aged_between_24_59_months']
        fields += ['has_women', 'aged_between_15_19_years', 'aged_between_20_49_years']
        for field in fields:
            assert self.browser.is_element_present_by_name(field)

    def get_investigator_values(self):
        return self.values

    def fill_valid_values(self):
        self.browser.find_by_id("location-value").value = Location.objects.create(name="Uganda").id
        self.values = {
            'surname': self.random_text('house'),
            'first_name': self.random_text('ayoyo'),
            'age': '25',
        }
        self.browser.fill_form(self.values)
        kampala = Location.objects.get(name="Kampala")
        kampala_county = Location.objects.get(name="Kampala County")
        investigator = Investigator.objects.get(name="Investigator name")
        self.fill_in_with_js('$("#location-district")', kampala.id)
        self.fill_in_with_js('$("#location-county")', kampala_county.id)
        self.fill_in_with_js('$("#household-investigator")', investigator.id)
        self.fill_in_with_js('$("#household-extra_resident_since_year")', 1984)
        self.fill_in_with_js('$("#household-extra_resident_since_month")', 1)

    def validate_household_created(self):
        assert self.browser.is_text_present("Household successfully registered.")

    def has_children(self, value):
        self.choose_radio('has_children', value)

    def are_children_fields_disabled(self, is_disabled=True):
        for element_id in ['aged_between_5_12_years', 'aged_between_13_17_years']:
            element_id = 'household-children-' + element_id
            assert self.is_disabled(element_id) == is_disabled
        self.are_children_below_5_fields_disabled(is_disabled=is_disabled)

    def is_no_below_5_checked(self):
        assert self.browser.find_by_id('household-children-has_children_below_5_1').selected == True

    def cannot_say_yes_to_below_5(self):
        assert self.is_disabled("household-children-has_children_below_5_0") == True
        self.are_children_fields_disabled()

    def has_children_below_5(self, value):
        self.choose_radio('has_children_below_5', value)

    def are_children_below_5_fields_disabled(self, is_disabled=True):
        for element_id in ['aged_between_0_5_months', 'aged_between_6_11_months', 'aged_between_12_23_months',
                           'aged_between_24_59_months']:
            element_id = 'household-children-' + element_id
            assert self.is_disabled(element_id) == is_disabled

    def has_women(self, value):
        self.choose_radio('has_women', value)

    def are_women_fields_disabled(self, is_disabled=True):
        for element_id in ['aged_between_15_19_years', 'aged_between_20_49_years']:
            element_id = 'household-women-' + element_id
            assert self.is_disabled(element_id) == is_disabled

    def fill_in_number_of_females_lower_than_sum_of_15_19_and_20_49(self):
        self.browser.fill('number_of_females', '1')
        self.browser.fill('aged_between_15_19_years', '2')
        self.browser.fill('aged_between_20_49_years', '3')

    def see_an_error_on_number_of_females(self):
        self.is_text_present(
            'Please enter a value that is greater or equal to the total number of women above 15 years age.')

    def choose_occupation(self, occupation_value):
        self.browser.select('occupation', occupation_value)

    def is_specify_visible(self, status=True):
        extra = self.browser.find_by_css('#extra-occupation-field')
        if status:
            assert len(extra) == 1
        else:
            assert len(extra) == 0


class AggregateStatusPage(PageObject):
    url = "/aggregates/status"

    def choose_location(self, locations):
        for key, value in locations.items():
            object_id = "location-%s" % key
            assert self.browser.is_element_present_by_id(object_id)
            jquery_id = '$("#%s")' % object_id
            location = Location.objects.get(name=value)
            self.fill_in_with_js(jquery_id, location.pk)

    def check_if_batches_present(self, *batches):
        all_options = self.browser.find_by_id('batch-list-select')[0].find_by_tag('option')
        all_options = [option.text for option in all_options]
        for batch in batches:
            assert batch.name in all_options

    def check_get_status_button_presence(self):
        assert self.browser.find_by_css("#aggregates-form")[0].find_by_tag('button')[0].text == "Get status"

    def choose_batch(self, batch):
        self.browser.select('batch', batch.pk)

    def assert_status_count(self, pending_households, completed_housesholds, pending_clusters, completed_clusters):
        assert self.browser.find_by_id('pending-households-count')[0].text == str(pending_households)
        assert self.browser.find_by_id('completed-households-count')[0].text == str(completed_housesholds)
        assert self.browser.find_by_id('pending-clusters-count')[0].text == str(pending_clusters)
        assert self.browser.find_by_id('completed-clusters-count')[0].text == str(completed_clusters)

    def check_presence_of_investigators(self, *investigators):
        for investigator in investigators:
            self.is_text_present(investigator.name)
            self.is_text_present(investigator.mobile_number)
            self.is_text_present("10")

    def assert_presence_of_batch_is_closed_message(self):
        self.is_text_present("This batch is currently closed for this location.")

    def select_all_district(self):
        self.browser.execute_script(
            "$('#location-district').val('').change().trigger('liszt:updated').chosen().change();")

    def see_all_districts_location_selected(self):
        assert self.browser.find_by_css('input[name=location]')[0].value == ''


class DownloadExcelPage(PageObject):
    url = "/aggregates/download_spreadsheet"

    def export_to_csv(self, batch):
        self.browser.select('batch', batch.pk)
        # self.submit()


class LoginPage(PageObject):
    url = "/accounts/login"

    def login(self, user):
        self.is_text_present('Type your username and password')

        user.set_password('secret')
        user.save()
        details = {'username': user.username,
                   'password': 'secret',
        }

        self.browser.fill_form(details)
        self.submit()

    def see_home_page_and_logout_link(self):
        assert self.browser.url == django_url(HomePage.url)
        self.see_logout_link()


class HomePage(PageObject):
    url = "/"

    def click_the_login_link(self):
        self.browser.click_link_by_text('login')

    def see_under_construction(self):
        self.is_text_present('Under Construction')


class LogoutPage(PageObject):
    url = "/accounts/logout"

    def check_browser_is_in_about_page(self):
        assert self.browser.url == django_url(AboutPage.url)


class AboutPage(PageObject):
    url = "/about/"

    def see_the_about_text_provided_by_panwar(self):
        self.is_text_present('Multiple Indicator Cluster Survey (MICS)')
        self.is_text_present('Survey tools')
        self.is_text_present('Mobile-based Multiple Indicator Cluster Survey (MICS)')


class BulkSMSPage(PageObject):
    url = "/bulk_sms"
    messages = {
        "location": "Please select a location.",
        "text": "Please enter the message to send.",
    }

    def compose_message(self, message):
        self.message = message
        self.fill('text', message)

    def select_locations(self, *locations):
        for location in locations:
            script = "$('#bulk-sms-locations').multiSelect('select', '%s')" % location.pk
            self.browser.execute_script(script)

    def is_message_sent(self):
        self.is_text_present("Your message has been sent to investigators.")
        for investgator in Investigator.objects.all():
            assert BackendMessage.objects.filter(identity=investgator.identity, text=self.message).count() == 1

    def error_message_for(self, field):
        self.is_text_present(self.messages[field])

    def enter_text(self, length):
        message = "*" * length
        self.fill('text', message)

    def counter_updated(self, length):
        counter = str(length) + "/480"
        self.is_text_present(counter)


class NewUserPage(PageObject):
    url = "/users/new/"

    def valid_page(self):
        sleep(5)
        self.is_text_present('New User')
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name',
                  'mobile_number', 'email', 'groups']
        for field in fields:
            assert self.browser.is_element_present_by_name(field)

    def fill_valid_values(self, data):
        self.browser.fill_form(data)
        sleep(2)

    def see_user_successfully_registered(self):
        sleep(0.5)
        self.is_text_present('User successfully registered.')

class BatchListPage(PageObject):
    url = "/batches/"

    def visit_batch(self, batch):
        self.browser.click_link_by_text("View")
        return BatchShowPage(self.browser, batch)


class BatchShowPage(object):
    def __init__(self, browser, batch):
        super(BatchShowPage, self).__init__()
        self.browser = browser
        self.url = "/batches/" + str(batch.pk)

    def batch_closed_for_all_locations(self):
        assert len(self.browser.find_by_css('input[checked=checked]')) == 0

    def open_batch_for(self, location):
        self.browser.execute_script('$($("input:checkbox")[0]).parent().bootstrapSwitch("toggleState")')
        sleep(2)

    def close_batch_for(self, location):
        self.browser.execute_script('$($("input:checkbox")[0]).parent().bootstrapSwitch("toggleState")')
        sleep(2)


class InvestigatorDetailsPage(PageObject):
    def __init__(self, browser, investigator):
        self.browser = browser
        self.investigator = investigator
        self.url = '/investigators/' + str(investigator.id) + '/'

    def validate_page_content(self):
        details = {
            'Name': self.investigator.name,
            'Mobile Number': self.investigator.mobile_number,
            'Age': str(self.investigator.age),
            'Sex': 'Male' if self.investigator.male else 'Female',
            'Highest Level of Education': self.investigator.level_of_education,
            'Preferred Language of Communication': self.investigator.language,
            'Country': 'Uganda',
            'City': 'Kampala',
        }
        for label, text in details.items():
            self.is_text_present(label)
            self.is_text_present(text)

    def validate_navigation_links(self):
        assert self.browser.find_link_by_text(' Back')
        assert self.browser.find_link_by_text(' Actions')

    def validate_back_link(self):
        self.browser.find_link_by_href(django_url(InvestigatorsListPage.url))
    
    def validate_detail_page_url(self):
        print self.browser.url
        assert self.browser.url == django_url(self.url)

    def validate_successful_edited_message(self):
        self.is_text_present("Investigator successfully edited.")


class UsersListPage(PageObject):
    url = "/users/"

    def validate_users_listed(self):
        self.is_text_present('Users List')

    def validate_displayed_headers(self):
        self.is_text_present("Full name")
        self.is_text_present("Role")
        self.is_text_present("Mobile number")
        self.is_text_present("Actions")

    def validate_users_paginated(self):
        self.browser.click_link_by_text("2")
        
    def assert_user_saved_sucessfully(self):
        self.is_text_present("User successfully edited.")

class UsersDetailsPage(PageObject):
    def set_user(self, user):
        self.user = user
        self.url = "/users/" + str(user.pk) + "/edit/"

    def assert_form_has_infomation(self):
        assert self.browser.find_by_name("username").first.value == self.user.username
        assert self.browser.find_by_name("mobile_number").first.value == self.user.userprofile.mobile_number
        assert self.browser.find_by_name("email").first.value == self.user.email

    def modify_users_information(self):
        self.fill('mobile_number', '994747474')

    def click_update_button(self):
        self.browser.find_by_name("save_button").first.click()

    def assert_user_saved_sucessfully(self):
        self.is_text_present("User successfully edited.")

    def assert_username_is_readonly(self):
        try:
            self.browser.find_by_css('#id_username[readonly]').first
            return True
        except Exception, e:
            return False
        
        
class EditInvestigatorPage(PageObject):
    def __init__(self, browser, investigator):
        self.browser = browser
        self.investigator = investigator
        self.url = '/investigators/' + str(investigator.id) + '/edit/'

    def validate_edit_investigator_url(self):
        assert self.browser.url == django_url(self.url)
        
    def change_name_of_investigator(self):
        self.values = {
            'name': 'Updated Name',
            'mobile_number': self.investigator.mobile_number,
            'confirm_mobile_number': self.investigator.mobile_number,
            'male': self.investigator.male,
            'age': self.investigator.age,
            'level_of_education': self.investigator.level_of_education,
            'language': self.investigator.language,
            'location': self.investigator.location,
            }
        self.browser.fill_form(self.values)

    def submit(self):
        self.browser.find_by_css("form button").first.click()

    def assert_user_saved_sucessfully(self):
        self.is_text_present("User successfully edited.")
