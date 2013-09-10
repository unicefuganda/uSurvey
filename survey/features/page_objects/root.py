# -*- coding: utf-8 -*-

from rapidsms.backends.database.models import BackendMessage

from survey.features.page_objects.base import PageObject
from survey.models.investigator import Investigator


class HomePage(PageObject):
    url = "/"

    def click_the_login_link(self):
        self.browser.click_link_by_text('login')

    def see_under_construction(self):
        self.is_text_present('Under Construction')


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