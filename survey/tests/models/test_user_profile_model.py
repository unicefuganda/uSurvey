from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, DatabaseError

from survey.models.users import UserProfile


class UserProfileTest(TestCase):

    def test_fields(self):
        user = UserProfile()
        fields = [str(item.attname) for item in user._meta.fields]
        self.assertEqual(len(fields), 5)
        for field in ['id', 'user_id', 'created', 'modified', 'mobile_number']:
            self.assertIn(field, fields)

    def test_store(self):
        user = User.objects.create()
        user_profile = UserProfile.objects.create(
            user=user, mobile_number='123456789')
        self.failUnless(user_profile.id)
        self.failUnless(user_profile.created)
        self.failUnless(user_profile.modified)
        self.assertEquals('123456789', user_profile.mobile_number)

    def test_mobile_number_is_unique(self):
        user = User.objects.create()
        UserProfile.objects.create(user=user, mobile_number="123456789")
        self.failUnlessRaises(
            IntegrityError, UserProfile.objects.create, mobile_number="123456789")

    def test_mobile_number_length_must_be_less_than_10(self):
        mobile_number_of_length_11 = "01234567891"
        self.failUnlessRaises(DatabaseError, UserProfile.objects.create,
                              mobile_number=mobile_number_of_length_11)
