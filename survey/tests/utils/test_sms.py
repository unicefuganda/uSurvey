from django.test import TestCase
from survey.models import *
from survey.utils.sms import send_sms

class SmsTest(TestCase):
    def test_send_sms(self):
        send_sms(None,None)