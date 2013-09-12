from datetime import date
from django.test.testcases import TestCase
from survey.forms.householdMember import HouseholdMemberForm


class HouseholdMemberFormTest(TestCase):
    def test_should_have_name_month_year_and_gender_fields(self):
        member_form = HouseholdMemberForm()

        fields = ['surname', 'first_name', 'date_of_birth', 'male']

        [self.assertIn(field, member_form.fields) for field in fields]

    def test_should_not_be_valid_if_name_field_is_empty_or_blank(self):
        member_form = HouseholdMemberForm()
        self.assertFalse(member_form.is_valid())

    def test_should_be_valid_if_all_fields_are_given(self):
        form_data = {'surname': 'xyz',
                     'date_of_birth': date(1980, 05, 01),
                     'Sex': True
        }

        member_form = HouseholdMemberForm(data=form_data)
        self.assertTrue(member_form.is_valid())