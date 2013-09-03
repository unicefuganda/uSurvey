# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from random import randint
from time import sleep
from lettuce.django import django_url

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

    def see_username_link(self, username):
        assert self.browser.find_link_by_text(username)

    def see_logout_link(self, username):
        self.browser.find_link_by_text(username).first.click()
        assert self.browser.find_link_by_text(" Logout")

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

    def see_user_settings_link(self, user):
        assert self.browser.find_link_by_partial_text("%s" % str(user.get_full_name()))

    def click_user_settings(self, user):
        self.browser.click_link_by_text("%s" % user.get_full_name())

    def assert_user_can_see_profile_and_logout_link(self):
        links = ["Edit Profile","Change Password","Logout"]
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

    def is_radio_selected(self,name,value):
        js = "$('input[name=%s]:radio').prop('checked')" %name
        return self.browser.execute_script(js) == value

    def see_success_message(self, object_name, action_str):
        self.is_text_present('%s successfully %s.' % (object_name, action_str))