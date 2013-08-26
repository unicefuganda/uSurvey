# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from time import sleep
from survey.features.page_objects.base import PageObject


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
        assert self.browser.find_by_name('mobile_number')
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

    def is_group_input_field_visible(self, status=True):
        if status:
            assert self.browser.find_by_name("groups")
        else:
            assert not self.browser.find_by_name("groups")


class NewUserPage(PageObject):
    url = "/users/new/"

    def valid_page(self):
        sleep(5)
        self.is_text_present('New User')
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name',
                  'mobile_number', 'email', 'groups']
        for field in fields:
            assert self.browser.is_element_present_by_name(field)

    def see_user_successfully_registered(self):
        sleep(0.5)
        self.is_text_present('User successfully registered.')