from django.template.defaultfilters import slugify
from datetime import date, datetime, timedelta
from django.test import TestCase
from mock import patch
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models.locations import *
from survey.models import HouseholdMemberGroup, GroupCondition, Question, Batch, HouseholdMemberBatchCompletion, NumericalAnswer, Survey, EnumerationArea
from survey.models.batch_question_order import BatchQuestionOrder
from survey.models.households import Household, HouseholdListing, HouseholdMember, SurveyHouseholdListing
from survey.models.backend import Backend
from survey.models.interviewer import Interviewer
from django.utils.timezone import utc


class HouseholdTest(TestCase):
    def setUp(self):
        self.country = LocationType.objects.create(name="Country", slug='country')
        self.district = LocationType.objects.create(name="District", parent=self.country,slug='district')
        self.county = LocationType.objects.create(name="County", parent=self.district,slug='county')
        self.subcounty = LocationType.objects.create(name="SubCounty", parent=self.county,slug='subcounty')
        self.parish = LocationType.objects.create(name="Parish", parent=self.subcounty,slug='parish')
        self.village = LocationType.objects.create(name="Village", parent=self.parish,slug='village')


        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(name="Kampala", type=self.district, parent=self.uganda)
        self.some_county = Location.objects.create(name="County", type=self.county, parent=self.kampala)
        self.some_sub_county = Location.objects.create(name="Subcounty", type=self.subcounty, parent=self.some_county)
        self.some_parish = Location.objects.create(name="Parish", type=self.parish, parent=self.some_sub_county)
        self.some_village = Location.objects.create(name="Village", type=self.village, parent=self.some_parish)
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(self.kampala)

        self.investigator = Interviewer.objects.create(name="Investigator",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)

        survey = Survey.objects.create(name="Test Survey",description="Desc",sample_size=10,has_sampling=True)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=survey)
        self.household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
#        fields_data = dict(surname='xyz', male=True, date_of_birth=date(1980, 05, 01), household=household)
        survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=survey)
        self.household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=self.household,survey_listing=survey_householdlisting,
                                                          registrar=self.investigator,registration_channel="ODK Access")

    # def test_location_hierarchy(self):
    #     self.assertEquals(self.household.location_hierarchy(), {'Country': self.uganda, 'City': self.kampala})

    def test_fields(self):
        hHead = Household()
        fields = [str(item.attname) for item in hHead._meta.fields]
        print fields
        self.assertEqual(len(fields), 10)
        print fields
        for field in ['id', 'created', 'modified', 'house_number', 'listing_id',
                      'physical_address', 'last_registrar_id', 'registration_channel', 'head_desc', 'head_sex']:
            self.assertIn(field, fields)

    def test_store(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A1243")
        investigator = Interviewer.objects.create(name="Investigator123",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        survey = Survey.objects.create(name="Test Survey3214",description="Desc234",sample_size=10,has_sampling=True)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=survey)
        household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=investigator,registration_channel="ODK Access",
                                             head_desc="Head",head_sex='MALE')
        self.failUnless(household.id)
        self.failUnless(household.created)
        self.failUnless(household.modified)

    def test_knows_next_uid_for_households(self):
        ea = EnumerationArea.objects.create(name="Kampala EA A1243")
        investigator = Interviewer.objects.create(name="Investigator123",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        survey = Survey.objects.create(name="Test Survey3214",description="Desc234",sample_size=10,has_sampling=True)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=survey)
        Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        self.assertEqual(123457, Household.next_new_house(household_listing))

    def test_knows_next_uid_for_households_if_survey_is_open_is_survey_dependent(self):
        open_survey = Survey.objects.create(name="Test Survey3214",description="Desc234",sample_size=10,has_sampling=True)

        ea = EnumerationArea.objects.create(name="Kampala EA A1243")
        investigator = Interviewer.objects.create(name="Investigator123",
                                                   ea=ea,
                                                   gender='1',level_of_education='Primary',
                                                   language='Eglish',weights=0)
        household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=open_survey)
        Household.objects.create(house_number=1234567,listing=household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        Household.objects.create(house_number=1234568,listing=household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
        Household.objects.create(house_number=1234569,listing=household_listing,physical_address='Test address',
                                             last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')

        self.assertEqual(1234570, Household.next_new_house(open_survey))
    # Eswar error in get_related_location
    # def test_should_know_household_related_location_to_village_level(self):
    #     country = LocationType.objects.create(name="Country1", slug='country')
    #     district = LocationType.objects.create(name="District1", parent=country,slug='district')
    #     county = LocationType.objects.create(name="County1", parent=district,slug='county')
    #     subcounty = LocationType.objects.create(name="SubCounty1", parent=county,slug='subcounty')
    #     parish = LocationType.objects.create(name="Parish1", parent=subcounty,slug='parish')
    #     village = LocationType.objects.create(name="Village1", parent=parish,slug='village')
    #
    #
    #     uganda = Location.objects.create(name="Uganda", type=country)
    #     kampala = Location.objects.create(name="Kampala", type=district, parent=uganda)
    #     some_county = Location.objects.create(name="Bukto", type=county, parent=kampala)
    #     some_sub_county = Location.objects.create(name="Some sub county", type=subcounty, parent=some_county)
    #     some_parish = Location.objects.create(name="Some parish", type=parish, parent=some_sub_county)
    #     some_village = Location.objects.create(name="Some village", type=village, parent=some_parish)
    #     ea = EnumerationArea.objects.create(name="Kampala EA A")
    #     ea.locations.add(kampala)
    #     open_survey = Survey.objects.create(name="Test Survey3214",description="Desc234",sample_size=10,has_sampling=True)
    #     investigator1 = Interviewer.objects.create(name="Investigator123",
    #                                                ea=ea,
    #                                                gender='1',level_of_education='Primary',
    #                                                language='Eglish',weights=0)
    #     household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=open_survey)
    #     household1 = Household.objects.create(house_number=1234567,listing=household_listing,physical_address='Test address',
    #                                          last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
    #     household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county',
    #                           'Parish': 'Some parish', 'Village': 'Some village'}
    #     self.assertEqual(household_location, household1.get_related_location())
    #
    # def test_should_know_how_to_set_household_location_given_a_set_of_households(self):
    #     country = LocationType.objects.create(name="Country1", slug='country')
    #     district = LocationType.objects.create(name="District1", parent=country,slug='district')
    #     county = LocationType.objects.create(name="County1", parent=district,slug='county')
    #     subcounty = LocationType.objects.create(name="SubCounty1", parent=county,slug='subcounty')
    #     parish = LocationType.objects.create(name="Parish1", parent=subcounty,slug='parish')
    #     village = LocationType.objects.create(name="Village1", parent=parish,slug='village')
    #
    #
    #     uganda = Location.objects.create(name="Uganda", type=country)
    #     kampala = Location.objects.create(name="Kampala", type=district, parent=uganda)
    #     some_county = Location.objects.create(name="Bukto", type=county, parent=kampala)
    #     some_sub_county = Location.objects.create(name="Some sub county", type=subcounty, parent=some_county)
    #     some_parish = Location.objects.create(name="Some parish", type=parish, parent=some_sub_county)
    #     some_village = Location.objects.create(name="Some village", type=village, parent=some_parish)
    #     ea = EnumerationArea.objects.create(name="Kampala EA A")
    #     ea.locations.add(kampala)
    #     open_survey = Survey.objects.create(name="Test Survey3214",description="Desc234",sample_size=10,has_sampling=True)
    #     investigator1 = Interviewer.objects.create(name="Investigator123",
    #                                                ea=ea,
    #                                                gender='1',level_of_education='Primary',
    #                                                language='Eglish',weights=0)
    #     household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=self.investigator,initial_survey=open_survey)
    #     household1 = Household.objects.create(house_number=1234567,listing=household_listing,physical_address='Test address',
    #                                          last_registrar=self.investigator,registration_channel="ODK Access",head_desc="Head",head_sex='MALE')
    #     household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county',
    #                           'Parish': 'Some parish', 'Village': 'Some village'}
    #
    #     households = Household.set_related_locations([household1])
    #
    #     self.assertEqual(household_location, households[0].related_locations)
    #
    # def test_get_location_for_some_hierarchy_returns_the_name_if_key_exists_in_location_hierarchy_dict(self):
    #     district = LocationType.objects.create(name="District", slug=slugify("district"))
    #     kampala_district = Location.objects.create(name="Kampala", type=district)
    #     ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
    #     ea.locations.add(kampala_district)
    #     investigator1 = Interviewer.objects.create(name="Investigator", mobile_number="987654321",
    #                                                 ea=ea,
    #                                                 backend=Backend.objects.create(name='something1'))
    #
    #     household1 = Household.objects.create(investigator=investigator1, uid=0)
    #
    #     location_hierarchy = {'District': kampala_district}
    #
    #     self.assertEqual(household1._get_related_location_name('District', location_hierarchy), kampala_district.name)
    #
    # def test_get_location_for_some_hierarchy_returns_empty_string_if_key_does_not_exist_in_location_hierarchy_dict(
    #         self):
    #     district = LocationType.objects.create(name="District", slug=slugify("district"))
    #     kampala_district = Location.objects.create(name="Kampala", type=district)
    #     ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
    #     ea.locations.add(kampala_district)
    #     investigator1 = Interviewer.objects.create(name="Investigator", mobile_number="987654321",
    #                                                 ea=ea,
    #                                                 backend=Backend.objects.create(name='something1'))
    #
    #     household1 = Household.objects.create(investigator=investigator1, uid=0)
    #
    #     location_hierarchy = {'District': kampala_district}
    #
    #     self.assertEqual(household1._get_related_location_name('County', location_hierarchy), "")
    #
    # def test_should_know_how_to_get_household_location_for_a_single_household(self):
    #     district = LocationType.objects.create(name="District", slug=slugify("district"))
    #     county = LocationType.objects.create(name="County", slug=slugify("county"))
    #     sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
    #     parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
    #     village = LocationType.objects.create(name="Village", slug=slugify("village"))
    #
    #     uganda = Location.objects.create(name="Uganda", type=self.country)
    #     kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
    #     bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
    #     some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
    #     some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
    #     some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)
    #     survey = Survey.objects.create(name="huhu")
    #     ea = EnumerationArea.objects.create(name="EA2", survey=survey)
    #     ea.locations.add(some_village)
    #
    #     investigator1 = Interviewer.objects.create(name="Investigator", mobile_number="987654321",
    #                                                 ea=ea,
    #                                                 backend=Backend.objects.create(name='something1'))
    #
    #     household1 = Household.objects.create(investigator=investigator1, ea=investigator1.ea, uid=0)
    #     household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county',
    #                           'Parish': 'Some parish', 'Village': 'Some village'}
    #
    #     self.assertEqual(household_location, household1.get_related_location())
    #
    # def test_should_know_who_is_household_head(self):
    #     village = LocationType.objects.create(name="Village", slug=slugify("village"))
    #     some_village = Location.objects.create(name="Some village", type=village)
    #     ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
    #     ea.locations.add(some_village)
    #     investigator = Interviewer.objects.create(name="Investigator", mobile_number="987654321",
    #                                                ea=ea,
    #                                                backend=Backend.objects.create(name='something1'))
    #     household = Household.objects.create(investigator=investigator, uid=0)
    #     fields_data = dict(surname='xyz', male=True, date_of_birth=date(2013, 05, 01), household=household)
    #
    #     hHead = HouseholdHead.objects.create(surname="Daddy", date_of_birth=date(1980, 05, 01), household=household)
    #     household_member = HouseholdMember.objects.create(**fields_data)
    #
    #     self.assertEqual(hHead, household.get_head())
    #     self.assertNotEqual(household_member, household.get_head())
    #
    # def test_should_return_all_households_members(self):
    #     hhold = Household.objects.create(investigator=Interviewer(), uid=0)
    #     household_head = HouseholdHead.objects.create(household=hhold, surname="Name", date_of_birth='1989-02-02')
    #     household_member1 = HouseholdMember.objects.create(household=hhold, surname="name", male=False,
    #                                                        date_of_birth='1989-02-02')
    #     household_member2 = HouseholdMember.objects.create(household=hhold, surname="name1", male=False,
    #                                                        date_of_birth='1989-02-02')
    #     all_members = hhold.all_members()
    #     self.assertTrue(household_head in all_members)
    #     self.assertTrue(household_member1 in all_members)
    #     self.assertTrue(household_member2 in all_members)
    #
    # def test_should_know_if_all_members_have_completed_currently_open_batches(self):
    #     backend = Backend.objects.create(name='something')
    #     kampala = Location.objects.create(name="Kampala")
    #     survey = Survey.objects.create(name="huhu")
    #     ea = EnumerationArea.objects.create(name="EA2", survey=survey)
    #     ea.locations.add(kampala)
    #
    #     investigator = Interviewer.objects.create(name="", mobile_number="123456789",
    #                                                ea=ea,
    #                                                backend=backend)
    #     hhold = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=0)
    #     household_head = HouseholdHead.objects.create(household=hhold, surname="Name", date_of_birth=date(1989, 2, 2))
    #     household_member1 = HouseholdMember.objects.create(household=hhold, surname="name2", male=False,
    #                                                        date_of_birth=date(1989, 2, 2))
    #     household_member2 = HouseholdMember.objects.create(household=hhold, surname="name3", male=False,
    #                                                        date_of_birth=date(1989, 2, 2))
    #     member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
    #     condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
    #     condition.groups.add(member_group)
    #     batch = Batch.objects.create(name="BATCH A", order=1)
    #     batch_2 = Batch.objects.create(name="BATCH B", order=2)
    #
    #     batch.open_for_location(investigator.location)
    #
    #     question_1 = Question.objects.create(identifier="identifier1",
    #                                          text="Question 1", answer_type='number',
    #                                          order=1, subquestion=False, group=member_group)
    #     question_1.batches.add(batch)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
    #
    #     member_list = [household_head, household_member1, household_member2]
    #
    #     self.assertFalse(hhold.completed_currently_open_batches())
    #     investigator.member_answered(question_1, household_member1, answer=1, batch=batch)
    #     self.assertFalse(hhold.completed_currently_open_batches())
    #     investigator.member_answered(question_1, household_member2, answer=1, batch=batch)
    #     self.assertFalse(hhold.completed_currently_open_batches())
    #     investigator.member_answered(question_1, household_head, answer=1, batch=batch)
    #     self.assertTrue(hhold.completed_currently_open_batches())
    #     self.assertEqual(3, HouseholdMemberBatchCompletion.objects.filter(batch=batch).count())
    #     [self.assertEqual(1, HouseholdMemberBatchCompletion.objects.filter(batch=batch, householdmember=member).count())
    #      for member in member_list]
    #
    # def test_household_knows_survey_can_be_retaken(self):
    #     member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
    #     condition = GroupCondition.objects.create(attribute="AGE", value=3, condition="GREATER_THAN")
    #     condition.groups.add(member_group)
    #     backend = Backend.objects.create(name='something')
    #     kampala = Location.objects.create(name="Kampala")
    #     survey = Survey.objects.create(name="huhu")
    #     ea = EnumerationArea.objects.create(name="EA2", survey=survey)
    #     ea.locations.add(kampala)
    #
    #     investigator = Interviewer.objects.create(name="", mobile_number="123456789",
    #                                                ea=ea,
    #                                                backend=backend)
    #
    #     household = Household.objects.create(investigator=investigator, uid=0)
    #
    #     household_member = HouseholdMember.objects.create(surname="Member",
    #                                                       date_of_birth=date(1980, 2, 2), male=False,
    #                                                       household=household)
    #     household_member_2 = HouseholdMember.objects.create(surname="Member 2",
    #                                                         date_of_birth=date(1980, 2, 2), male=False,
    #                                                         household=household)
    #     batch = Batch.objects.create(name="BATCH A", order=1)
    #     batch_2 = Batch.objects.create(name="BATCH A", order=1)
    #
    #     batch.open_for_location(investigator.location)
    #     batch_2.open_for_location(investigator.location)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
    #                                                   investigator=investigator, household=household_member.household)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
    #                                                   investigator=investigator, household=household_member.household)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
    #                                                   investigator=investigator, household=household_member.household)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
    #                                                   investigator=investigator, household=household_member.household)
    #
    #     self.assertTrue(household.can_retake_survey(batch, 5))
    #     self.assertTrue(household.can_retake_survey(batch_2, 5))
    #
    #     HouseholdMemberBatchCompletion.objects.all().delete()
    #
    #     ten_minutes_ago = datetime.utcnow().replace(tzinfo=utc) - timedelta(minutes=10)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
    #                                                   investigator=investigator, household=household_member.household,
    #                                                   created=ten_minutes_ago)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
    #                                                   investigator=investigator, household=household_member.household,
    #                                                   created=ten_minutes_ago)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
    #                                                   investigator=investigator, household=household_member.household)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
    #                                                   investigator=investigator, household=household_member.household)
    #     self.assertFalse(household.can_retake_survey(batch, 5))
    #     self.assertTrue(household.can_retake_survey(batch_2, 5))
    #
    #     HouseholdMemberBatchCompletion.objects.all().delete()
    #
    #     three_minutes_ago = datetime.utcnow().replace(tzinfo=utc) - timedelta(minutes=3)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
    #                                                   investigator=investigator, household=household_member.household,
    #                                                   created=ten_minutes_ago)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
    #                                                   investigator=investigator, household=household_member.household,
    #                                                   created=three_minutes_ago)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
    #                                                   investigator=investigator, household=household_member.household,
    #                                                   created=three_minutes_ago)
    #
    #     HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
    #                                                   investigator=investigator, household=household_member.household,
    #                                                   created=ten_minutes_ago)
    #     self.assertTrue(household.can_retake_survey(batch, 5))
    #     self.assertTrue(household.can_retake_survey(batch_2, 5))
    #
    # def test_last_answered(self):
    #     self.batch = Batch.objects.create(order=1, name="Batch Name")
    #     self.another_batch = Batch.objects.create(order=2, name="Batch Name 2")
    #
    #     self.batch.open_for_location(self.investigator.location)
    #     batch_question_1 = Question.objects.create(order=1, text="Test question 1",
    #                                                answer_type=Question.NUMBER, group=self.member_group)
    #     question_2 = Question.objects.create(order=2, text="Test question 2",
    #                                          answer_type=Question.NUMBER, group=self.member_group)
    #     batch_question_1.batches.add(self.batch)
    #     question_2.batches.add(self.batch)
    #
    #     BatchQuestionOrder.objects.create(question=batch_question_1, batch=self.batch, order=1)
    #     BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)
    #
    #     self.investigator.member_answered(batch_question_1, self.household_member, 1, self.batch)
    #     self.assertEqual(batch_question_1.text, self.household_member.last_question_answered().text)
    #
    # def test_retake_latest_batch(self):
    #     batch_1 = Batch.objects.create(order=1)
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #     question_1.batches.add(batch_1)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=batch_1, order=1)
    #
    #     batch_1.open_for_location(self.investigator.location)
    #     self.investigator.member_answered(question_1, self.household_member, 1, batch_1)
    #     batch_1.close_for_location(self.investigator.location)
    #
    #     batch_2 = Batch.objects.create(order=2)
    #
    #     question_2 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #     question_2.batches.add(batch_2)
    #     BatchQuestionOrder.objects.create(question=question_2, batch=batch_2, order=1)
    #
    #     batch_2.open_for_location(self.investigator.location)
    #     self.investigator.member_answered(question_2, self.household_member, 1, batch_2)
    #
    #     self.assertEquals(NumericalAnswer.objects.count(), 2)
    #
    #     self.household.retake_latest_batch()
    #
    #     self.assertEquals(NumericalAnswer.objects.count(), 1)
    #
    # def test_has_pending_survey(self):
    #     batch = Batch.objects.create(order=1)
    #     batch.open_for_location(self.kampala)
    #
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #     question_2 = Question.objects.create(text="How many of them are male?",
    #                                          answer_type=Question.NUMBER, order=2, group=self.member_group)
    #     question_1.batches.add(batch)
    #     question_2.batches.add(batch)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
    #     BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
    #
    #     self.assertTrue(self.household.has_pending_survey())
    #
    #     self.investigator.member_answered(question_1, self.household_member, 1, batch)
    #
    #     self.assertTrue(self.household.has_pending_survey())
    #
    #     self.investigator.member_answered(question_2, self.household_member, 1, batch)
    #
    #     self.assertFalse(self.household.has_pending_survey())
    #
    # def test_knows_last_question_answered_by_household_and_household_has_next_question(self):
    #     batch = Batch.objects.create(order=1)
    #     batch.open_for_location(self.kampala)
    #
    #     question_1 = Question.objects.create(text="How many members are there in this household?",
    #                                          answer_type=Question.NUMBER, order=1, group=self.member_group)
    #     question_2 = Question.objects.create(text="How many of them are male?",
    #                                          answer_type=Question.NUMBER, order=2, group=self.member_group)
    #     question_1.batches.add(batch)
    #     question_2.batches.add(batch)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
    #     BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
    #
    #     self.assertIsNone(self.household.last_question_answered())
    #     self.assertFalse(self.household.has_completed_batches([batch]))
    #
    #     self.investigator.member_answered(question_1, self.household_member, 1, batch)
    #
    #     self.assertEqual(question_1, self.household.last_question_answered())
    #     self.assertTrue(self.household.has_next_question(batch))
    #     self.assertFalse(self.household.survey_completed())
    #
    #     self.investigator.member_answered(question_2, self.household_member, 1, batch)
    #     self.assertEqual(question_2, self.household.last_question_answered())
    #     self.assertFalse(self.household.has_next_question(batch))
    #     self.assertTrue(self.household.survey_completed())
    #     self.assertTrue(self.household.has_completed_batches([batch]))
    #
    # def test_knows_to_mark_answers_as_old(self):
    #     investigator = Interviewer.objects.create(name="inv1", ea=self.ea,
    #                                                backend=self.backend)
    #     household = Household.objects.create(investigator=investigator, ea=investigator.ea, uid=0)
    #     household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
    #                                                       male=False,
    #                                                       household=household)
    #
    #     batch = Batch.objects.create(name="Batch 1", order=1)
    #     group = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
    #     group_condition = GroupCondition.objects.create(attribute="GENDER", condition="EQUALS", value=True)
    #     group_condition.groups.add(group)
    #
    #     question_1 = Question.objects.create(group=group, text="This is another question", answer_type="number",
    #                                          order=1)
    #     question_1.batches.add(batch)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
    #
    #     batch.open_for_location(investigator.location)
    #     investigator.member_answered(question_1, household_member, 1, batch)
    #
    #     self.assertFalse(NumericalAnswer.objects.filter(question=question_1)[0].is_old)
    #
    #     household.mark_past_answers_as_old()
    #
    #     self.assertTrue(NumericalAnswer.objects.filter(question=question_1)[0].is_old)
    #
    # def test_should_know_total_households_in_location(self):
    #     open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
    #     Household.objects.all().delete()
    #     kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)
    #     ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
    #     ea.locations.add(kampala_city)
    #     investigator_1 = Interviewer.objects.create(name='some_inv', mobile_number='123456783', male=True,
    #                                                  ea=self.ea)
    #     investigator_2 = Interviewer.objects.create(name='some_inv', mobile_number='123456781', male=True,
    #                                                  ea=ea)
    #
    #     household_1 = Household.objects.create(investigator=investigator_1, ea=investigator_1.ea, survey=open_survey)
    #     household_2 = Household.objects.create(investigator=investigator_2, ea=investigator_2.ea,
    #                                            survey=open_survey)
    #
    #     self.assertEqual(2, Household.all_households_in(self.uganda, open_survey).count())
    #     self.assertIn(household_1, Household.all_households_in(self.uganda, open_survey))
    #     self.assertIn(household_2, Household.all_households_in(self.uganda, open_survey))
    #
    # def test_should_know_number_of_members_interviewed(self):
    #     self.batch = Batch.objects.create(name="BATCH A", order=1)
    #     Household.objects.all().delete()
    #     member_group = HouseholdMemberGroup.objects.create(name='group1', order=1)
    #     question = Question.objects.create(text="some question", answer_type=Question.NUMBER, order=1,
    #                                        group=member_group)
    #     self.batch.questions.add(question)
    #     BatchQuestionOrder.objects.create(question=question, batch=self.batch, order=1)
    #
    #     self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)
    #
    #     investigator_1 = Interviewer.objects.create(name='some_inv', mobile_number='123456783', male=True,
    #                                                  ea=self.ea)
    #
    #     household_1 = Household.objects.create(investigator=investigator_1, ea=investigator_1.ea)
    #     member_1 = HouseholdMember.objects.create(household=household_1, date_of_birth=date(2000, 02, 02))
    #     member_2 = HouseholdMember.objects.create(household=household_1, date_of_birth=date(2000, 02, 02))
    #     member_3 = HouseholdMember.objects.create(household=household_1, date_of_birth=date(2000, 02, 02))
    #
    #     investigator_1.member_answered(question, member_1, 1, self.batch)
    #
    #     self.assertIn(member_1, household_1.members_interviewed(self.batch))
    #
    # def test_should_return_0_members_interviewed_if_no_question_in_batch(self):
    #     self.batch = Batch.objects.create(name="BATCH A", order=1)
    #     Household.objects.all().delete()
    #     self.kampala_city = Location.objects.create(name='Kampala City', tree_parent=self.kampala, type=self.city)
    #
    #     investigator_1 = Interviewer.objects.create(name='some_inv', mobile_number='123456783', male=True,
    #                                                  ea=self.ea)
    #
    #     household_1 = Household.objects.create(investigator=investigator_1, ea=investigator_1.ea)
    #     HouseholdMember.objects.create(household=household_1, date_of_birth=datetime(2000, 02, 02))
    #     HouseholdMember.objects.create(household=household_1, date_of_birth=datetime(2000, 02, 02))
    #     HouseholdMember.objects.create(household=household_1, date_of_birth=datetime(2000, 02, 02))
    #
    #     self.assertEqual(0, len(household_1.members_interviewed(self.batch)))
    #
    # def test_should_create_batch_completion_entry(self):
    #     investigator_1 = Interviewer.objects.create(name='some_inv', mobile_number='123456783', male=True,
    #                                                  ea=self.ea)
    #     household = Household.objects.create(uid='123', investigator=investigator_1, ea=investigator_1.ea)
    #     batch = Batch.objects.create(name="batch hoho")
    #     household.batch_completed(batch)
    #     self.assertEqual(1, household.batch_completion_batches.filter(batch=batch, investigator=investigator_1).count())
    #     household.batch_completed(None)
    #     self.assertEqual(1, household.batch_completion_batches.filter(batch=batch, investigator=investigator_1).count())
    #
    # def test_get_non_complete_members(self):
    #     investigator_1 = Interviewer.objects.create(name='some_inv', mobile_number='123456783', male=True,
    #                                                  ea=self.ea)
    #     household_1 = Household.objects.create(uid='123', investigator=investigator_1, ea=investigator_1.ea)
    #     member_1 = HouseholdMember.objects.create(surname="Member 1", household=household_1, date_of_birth=datetime(2000, 02, 02))
    #     member_2 = HouseholdMember.objects.create(surname="Member 2", household=household_1, date_of_birth=datetime(2000, 02, 02))
    #     batch = Batch.objects.create(name="batch hoho")
    #
    #     HouseholdMemberBatchCompletion.objects.create(household=household_1, householdmember=member_1, batch=batch,
    #                                                   investigator=investigator_1)
    #
    #     self.assertEqual(1, len(household_1.get_non_complete_members()))
    #     self.assertIn(member_2, household_1.get_non_complete_members())
    #     self.assertNotIn(member_1, household_1.get_non_complete_members())
    #
    # def test_knows_some_members_are_not_complete(self):
    #     investigator_1 = Interviewer.objects.create(name='some_inv', mobile_number='123456783', male=True,
    #                                                  ea=self.ea)
    #     household_1 = Household.objects.create(uid='123', investigator=investigator_1, ea=investigator_1.ea)
    #     member_1 = HouseholdMember.objects.create(surname="Member 1", household=household_1, date_of_birth=datetime(2000, 02, 02))
    #     member_2 = HouseholdMember.objects.create(surname="Member 2", household=household_1, date_of_birth=datetime(2000, 02, 02))
    #     batch = Batch.objects.create(name="batch hoho")
    #
    #     HouseholdMemberBatchCompletion.objects.create(household=household_1, householdmember=member_1, batch=batch,
    #                                                   investigator=investigator_1)
    #     self.assertTrue(household_1.has_some_members_who_completed())
    #
    #     HouseholdMemberBatchCompletion.objects.create(household=household_1, householdmember=member_2, batch=batch,
    #                                                   investigator=investigator_1)
    #     self.assertFalse(household_1.has_some_members_who_completed())
    #
    # def test_knows_number_of_households_in_an_ea(self):
    #     kisasi = Location.objects.create(name="Kisasi", type=self.city, tree_parent=self.uganda)
    #     ea = EnumerationArea.objects.create(name="EA2", survey=self.survey)
    #     ea.locations.add(kisasi)
    #
    #     investigator_1 = Interviewer.objects.create(name='some_inv', mobile_number='123456783', male=True, ea=self.ea)
    #     household_1 = Household.objects.create(uid='123', investigator=investigator_1, ea=investigator_1.ea,
    #                                            survey=self.survey)
    #     household_3 = Household.objects.create(uid='123', investigator=investigator_1, survey=self.survey, ea=ea)
    #
    #     households_in_ea = Household.all_households_in(self.uganda, self.survey, ea=self.ea)
    #     self.assertEqual(households_in_ea.count(), 2)
    #     self.assertIn(household_1, households_in_ea)
    #     self.assertIn(self.household, households_in_ea)
    #     self.assertNotIn(household_3, households_in_ea)