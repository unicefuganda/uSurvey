# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from django.test import TestCase
from survey.models import RandomHouseHoldSelection


class RandomHouseHoldSelectionTest(TestCase):
    def test_store(self):
        selection = RandomHouseHoldSelection.objects.create(mobile_number="123456789", no_of_households=50,
                                                            selected_households="1,2,3,4,5,6,7,8,9,10")
        self.failUnless(selection.id)