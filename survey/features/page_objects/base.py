# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from random import randint
from time import sleep
from django.core.urlresolvers import reverse
from lettuce.django import django_url
from nose.tools import assert_equals

class PageObject(object):
    def __init__(self, browser):
        self.browser = browser

    def visit(self):
        self.browser.visit(django_url(self.url))

    def validate_url(self):
        assert self.browser.url == django_url(self.url)

    def random_text(self, text):
        return text + str(randint(1, 999))

    def fill(self, name, value):
        self.browser.fill(name, value)

    def is_text_present(self, text, status=True):
        assert_equals(status, self.browser.is_text_present(text))

    def is_disabled(self, element_id):
        try:
            element = self.browser.find_by_css('#%s[disabled]' % element_id).first
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

    def see_username_link(self):
        assert self.browser.find_by_css("#drop-user-settings")

    def see_logout_link(self):
        self.click_by_css('#drop-user-settings')
        assert self.browser.find_link_by_text(" Logout")

    def see_the_about_link(self):
        assert self.browser.find_link_by_text('About')

    def find_link_by_text(self,text):
        assert self.browser.find_link_by_text(text)

    def click_the_about_link(self):
        self.browser.click_link_by_text('About')

    def check_anonymous_user_allowed_tabs(self):
        assert self.browser.find_link_by_text('About')
        assert self.browser.find_link_by_text('mMICS')
        assert self.browser.find_link_by_text('Login')

    def check_data_entry_allowed_tabs(self):
        assert self.browser.find_link_by_text('About')
        assert self.browser.find_link_by_text('mMICS')
        assert self.browser.find_link_by_text('Survey Administration')
        assert self.browser.find_link_by_text('Analysis')

    def check_researcher_allowed_tabs(self):
        self.check_data_entry_allowed_tabs()
        assert self.browser.find_link_by_text('Downloads')

    def check_all_tabs(self):
        self.check_researcher_allowed_tabs()
        assert self.browser.find_link_by_text('Settings')

    def check_researcher_not_allowed_tabs(self):
        assert not self.browser.find_link_by_text('Settings')

    def check_data_entry_not_allowed_tabs(self):
        self.check_researcher_not_allowed_tabs()
        assert not self.browser.find_link_by_text('Downloads')

    def check_anonymous_user_not_allowed_tabs(self):
        self.check_data_entry_not_allowed_tabs()
        assert not self.browser.find_link_by_text('Survey Administration')

    def check_notify_investigators_drop_down_is_not_present(self):
        self.browser.click_link_by_text('Survey Administration')
        assert not self.browser.find_link_by_text('Notifications')

    def choose_radio(self, name, value):
        js = "$('input:radio[name=%s][value=%s]').prop('checked', true).change()" % (name, value)
        self.browser.execute_script(js)

    def see_user_settings_link(self, user):
        assert self.browser.find_link_by_partial_text("%s" % str(user.get_full_name()))

    def click_user_settings(self, user):
        self.click_by_css("#drop-user-settings")

    def assert_user_can_see_profile_and_logout_link(self):
        links = ["Edit Profile", "Change Password", "Logout"]
        for link in links:
            assert self.browser.find_link_by_partial_text(link)

    def click_reset_password_form(self):
        self.browser.find_link_by_partial_text("Change Password").click()

    def assert_password_successfully_reset(self):
        self.browser.is_text_present("Your password was reset successfully!!")

    def click_actions_button(self):
        self.browser.find_by_css('#action_caret').first.click()

    def click_link_by_text(self, text):
        self.browser.click_link_by_text(text)

    def fill_valid_values(self, data):
        self.browser.fill_form(data)
        sleep(2)

    def validate_pagination(self):
        self.browser.click_link_by_text("2")

    def is_radio_selected(self, name, value):
        js = "$('input[name=%s]:radio').prop('checked')" % name
        return self.browser.execute_script(js) == value

    def see_success_message(self, object_name, action_str):
        self.is_text_present('%s successfully %s.' % (object_name, action_str))

    def select_multiple(self, field_id=None, *data):
        for item in data:
            script = "$('%s').multiSelect('select', '%s')" % (field_id, item.pk)
            self.browser.execute_script(script)

    def validate_fields_present(self, fields, status=True):
        for field in fields:
            self.is_text_present(field, status)

    def select_date(self, field_id):
        script = "$('%s').focus()" % field_id
        self.browser.execute_script(script)
        script = "$('.ui-state-default').first().click()"
        self.browser.execute_script(script)

    def click_tab(self, tab_name):
        self.browser.click_link_by_text(tab_name)

    def see_dropdown(self, links):
        for url_name in links:
            assert self.browser.find_link_by_partial_href(reverse(url_name))

    def select(self, name, values):
        for value in values:
            self.browser.select(name, value)

    def click_by_css(self, css_selector):
        self.browser.find_by_css(css_selector).first.click()

    def click_link_by_partial_href(self, modal_id):
        self.browser.click_link_by_partial_href(modal_id)

    def click_link_by_href(self, modal_id):
        self.browser.click_link_by_href(modal_id)

    def click_button(self, name):
        self.browser.find_by_name(name).first.click()

    def find_by_css(self, css_selector, text):
        assert self.browser.find_by_css(css_selector).first.value == text

    def see_select_option(self, option_list, field_name):
        for option in option_list:
            assert option in self.browser.find_by_name(field_name).first.text

    def option_not_present(self, option_list, field_name):
        for option in option_list:
            assert not option in self.browser.find_by_name(field_name).first.text

    def see_message(self, text):
        assert self.browser.is_text_present(text)

    def see_confirm_modal_message(self, name, action_str="delete"):
        self.is_text_present("Confirm: Are you sure you want to %s %s?" % (action_str, name))

    def validate_form_present(self, form):
        for key in form.keys():
            assert self.browser.find_by_name(key).first
            self.is_text_present(form[key])

    def validate_form_values(self, form_values):
        for key in form_values.keys():
            assert self.browser.find_by_name(key).first.value == str(form_values[key])

    def field_not_present(self, field_name):
        assert not self.browser.find_by_name(field_name)

    def field_is_visible(self, field_name):
        return self.browser.find_by_name(field_name).first.visible

    def find_element_by_css(self, selector):
        assert self.browser.find_by_css(selector).first

    def is_hidden(self, field, status=True):
        assert_equals(status, not self.browser.find_by_css('.hide').first.visible)

    def find_by_name(self,name):
        assert self.browser.find_by_name(name)

    def click_by_name(self,name):
        self.browser.find_by_name(name).first.click()

    def input_file(self, filename):
        self.browser.attach_file('file', filename)