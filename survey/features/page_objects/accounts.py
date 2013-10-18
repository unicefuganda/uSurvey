# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from survey.features.page_objects.base import PageObject
from survey.features.page_objects.root import AboutPage, HomePage

from lettuce.django import django_url


class ResetPasswordPage(PageObject):
    url = '/accounts/reset_password/'

    def is_change_password_form_visble(self):
        self.browser.is_text_present("Old password")
        self.browser.is_text_present("New password")
        self.browser.is_text_present("New password confirmation")

    def click_change_password_button(self):
        self.browser.find_by_name("save_changes").first.click()

    def is_incorrect_oldpassword_error_visible(self):
        self.is_text_present("Your old password was entered incorrectly. Please enter it again.")

    def is_password_mismatch(self):
        self.is_text_present("The two password fields didn't match.")


class LogoutPage(PageObject):
    url = "/accounts/logout"

    def check_browser_is_in_about_page(self):
        assert self.browser.url == django_url(AboutPage.url)


class LoginPage(PageObject):
    url = "/accounts/login"

    def login(self, user):
        self.is_text_present('Type your username and password to login')

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