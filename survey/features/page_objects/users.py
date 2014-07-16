# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from time import sleep
from lettuce.django import django_url
from survey.features.page_objects.base import PageObject


class UsersListPage(PageObject):
    url = "/users/"

    def validate_users_listed(self):
        self.is_text_present('Users List')

    def validate_displayed_headers(self):
        self.validate_fields_present(["Full name", "Role", "Mobile number", "Actions"])

    def validate_users_paginated(self):
        self.browser.click_link_by_text("2")

    def assert_user_saved_sucessfully(self):
        self.is_text_present("User successfully edited.")


class EditUserDetailsPage(PageObject):
    def set_user(self, user):
        self.user = user
        self.url = "/users/" + str(user.pk) + "/edit/"

    def assert_form_has_infomation(self):
        assert self.browser.find_by_name("username").first.value == self.user.username
        assert self.browser.find_by_name("mobile_number").first.value == self.user.userprofile.mobile_number
        assert self.browser.find_by_name("email").first.value == self.user.email

    def modify_users_information(self):
        assert self.browser.find_by_name('mobile_number')
        assert self.browser.find_by_name('password')
        assert self.browser.find_by_name('confirm_password')
        self.fill('mobile_number', '994747474')
        self.fill('password', 'password')
        self.fill('confirm_password', 'password')


    def click_update_button(self):
        self.browser.find_by_name("save_button").first.click()

    def assert_user_saved_sucessfully(self):
        self.is_text_present("User successfully edited.")

    def assert_username_is_readonly(self):
        try:
           assert self.browser.find_by_css('#id_username[readonly]').first
        except Exception, e:
            return False

    def is_group_input_field_visible(self, status=True):
        if status:
            assert self.browser.find_by_name("groups")
        else:
            assert not self.browser.find_by_name("groups")

class UserDetailsPage(PageObject):

    def __init__(self, browser, user):
        self.browser = browser
        self.user = user
        self.url = '/users/%d/'%user.id

    def validate_page_content(self):
        details = {
            'Username': self.user.username,
            'First name': self.user.first_name,
            'Last name': self.user.last_name,
            'Mobile number': self.user.userprofile.mobile_number,
            'Email': self.user.email,
            'Groups': ", ".join(self.user.groups.all().values_list('name', flat=True)),
            }
        for label, text in details.items():
            self.is_text_present(label)
            self.is_text_present(text)

    def validate_back_link(self):
        self.browser.find_link_by_href(django_url(UsersListPage.url))


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