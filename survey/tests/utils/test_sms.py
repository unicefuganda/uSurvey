from django.test import TestCase
from survey.models import *
from survey.utils.sms import send_sms

class SmsTest(TestCase):
	def test_send_sms(self):
		# mobile_number = 0123456789
		# msg = "Enter Message"
		# self.assertEqual(mobile_number, 0123456789)
		# self.assertEqual(msg, "Enter Message")
		send_sms(None,None)