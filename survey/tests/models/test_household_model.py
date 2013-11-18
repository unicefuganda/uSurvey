from django.template.defaultfilters import slugify
from datetime import date, datetime, timedelta
from django.test import TestCase
from mock import patch
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import HouseholdMemberGroup, GroupCondition, Question, Batch, HouseholdMemberBatchCompletion, NumericalAnswer, BatchQuestionOrder, Survey
from survey.models.households import Household, HouseholdHead, HouseholdMember
from survey.models.backend import Backend
from survey.models.investigator import Investigator
from django.utils.timezone import utc


class HouseholdTest(TestCase):

    def setUp(self):
        self.member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=11)
        self.condition = GroupCondition.objects.create(attribute="AGE", value=4, condition="GREATER_THAN")
        self.condition.groups.add(self.member_group)
        self.backend = Backend.objects.create(name='something backend')
        self.country = LocationType.objects.create(name="Country", slug=slugify("country"))
        self.city = LocationType.objects.create(name="City", slug=slugify("city"))
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.kampala = Location.objects.create(name="Kampala", type=self.city, tree_parent=self.uganda)
        self.investigator = Investigator.objects.create(name="", mobile_number="123456788",
                                                  location=self.kampala,
                                                  backend=self.backend)

        self.household = Household.objects.create(investigator=self.investigator, location=self.investigator.location, uid=100)

        self.household_member = HouseholdMember.objects.create(surname="Member",
                                                            date_of_birth=date(1980, 2, 2), male=False, household=self.household)

    def test_location_hierarchy(self):
        self.assertEquals(self.household.location_hierarchy(), {'Country': self.uganda, 'City': self.kampala})

    def test_fields(self):
        hHead = Household()
        fields = [str(item.attname) for item in hHead._meta.fields]
        self.assertEqual(len(fields), 9)
        for field in ['id', 'investigator_id', 'created', 'modified', 'uid', 'location_id', 'random_sample_number',
                      'survey_id', 'household_code']:
            self.assertIn(field, fields)

    def test_store(self):
        hhold = Household.objects.create(investigator=Investigator(), uid=0)
        self.failUnless(hhold.id)
        self.failUnless(hhold.created)
        self.failUnless(hhold.modified)
        self.assertEquals(0, hhold.uid)

    def test_knows_next_uid_for_households(self):
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", backend=Backend.objects.create(name='something1'))
        Household.objects.create(investigator=investigator, uid=101)
        self.assertEqual(102, Household.next_uid())

    def test_knows_next_uid_for_households_if_survey_is_open_is_survey_dependent(self):
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        with patch.object(Survey, "currently_open_survey", return_value=open_survey):
            investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", backend=Backend.objects.create(name='something1'))
            Household.objects.create(investigator=investigator, survey=open_survey, uid=101)
            Household.objects.create(investigator=investigator, survey=open_survey, uid=102)
            Household.objects.create(investigator=investigator, uid=103)

            self.assertEqual(103, Household.next_uid(open_survey))

    def test_should_know_household_related_location_to_village_level(self):
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        county = LocationType.objects.create(name="County", slug=slugify("county"))
        sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
        parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
        village = LocationType.objects.create(name="Village", slug=slugify("village"))

        uganda = Location.objects.create(name="Uganda", type=self.country)
        kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
        some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
        some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
        some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, location=investigator1.location, uid=0)
        household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county', 'Parish': 'Some parish', 'Village': 'Some village'}

        self.assertEqual(household_location, household1.get_related_location())

    def test_should_know_how_to_set_household_location_given_a_set_of_households(self):
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        county = LocationType.objects.create(name="County", slug=slugify("county"))
        sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
        parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
        village = LocationType.objects.create(name="Village", slug=slugify("village"))

        uganda = Location.objects.create(name="Uganda", type=self.country)
        kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
        some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
        some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
        some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, location=investigator1.location, uid=0)
        household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county', 'Parish': 'Some parish', 'Village': 'Some village'}

        households = Household.set_related_locations([household1])

        self.assertEqual(household_location, households[0].related_locations)

    def test_get_location_for_some_hierarchy_returns_the_name_if_key_exists_in_location_hierarchy_dict(self):
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        kampala_district = Location.objects.create(name="Kampala", type=district)
        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=kampala_district, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, uid=0)

        location_hierarchy = {'District': kampala_district}

        self.assertEqual(household1._get_related_location_name('District', location_hierarchy), kampala_district.name)

    def test_get_location_for_some_hierarchy_returns_empty_string_if_key_does_not_exist_in_location_hierarchy_dict(self):
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        kampala_district = Location.objects.create(name="Kampala", type=district)
        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=kampala_district, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, uid=0)

        location_hierarchy = {'District': kampala_district}

        self.assertEqual(household1._get_related_location_name('County', location_hierarchy), "")

    def test_should_know_how_to_get_household_location_for_a_single_household(self):
        district = LocationType.objects.create(name="District", slug=slugify("district"))
        county = LocationType.objects.create(name="County", slug=slugify("county"))
        sub_county = LocationType.objects.create(name="Subcounty", slug=slugify("sub-county"))
        parish = LocationType.objects.create(name="Parish", slug=slugify("parish"))
        village = LocationType.objects.create(name="Village", slug=slugify("village"))

        uganda = Location.objects.create(name="Uganda", type=self.country)
        kampala_district = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)
        bukoto_county = Location.objects.create(name="Bukoto", type=county, tree_parent=kampala_district)
        some_sub_county = Location.objects.create(name="Some sub county", type=sub_county, tree_parent=bukoto_county)
        some_parish = Location.objects.create(name="Some parish", type=parish, tree_parent=some_sub_county)
        some_village = Location.objects.create(name="Some village", type=village, tree_parent=some_parish)

        investigator1 = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))

        household1 = Household.objects.create(investigator=investigator1, location=investigator1.location, uid=0)
        household_location = {'District': 'Kampala', 'County': 'Bukoto', 'Subcounty': 'Some sub county', 'Parish': 'Some parish', 'Village': 'Some village'}

        self.assertEqual(household_location, household1.get_related_location())

    def test_should_know_who_is_household_head(self):
        village = LocationType.objects.create(name="Village", slug=slugify("village"))
        some_village = Location.objects.create(name="Some village", type=village)
        investigator = Investigator.objects.create(name="Investigator", mobile_number="987654321", location=some_village, backend=Backend.objects.create(name='something1'))
        household = Household.objects.create(investigator=investigator, uid=0)
        fields_data = dict(surname='xyz', male=True, date_of_birth=date(2013, 05, 01), household=household)

        hHead = HouseholdHead.objects.create(surname="Daddy", date_of_birth=date(1980, 05, 01), household=household)
        household_member = HouseholdMember.objects.create(**fields_data)

        self.assertEqual(hHead, household.get_head())
        self.assertNotEqual(household_member, household.get_head())

    def test_should_return_all_households_members(self):
        hhold = Household.objects.create(investigator=Investigator(), uid=0)
        household_head = HouseholdHead.objects.create(household=hhold,surname="Name", date_of_birth='1989-02-02')
        household_member1 = HouseholdMember.objects.create(household=hhold, surname="name", male=False, date_of_birth='1989-02-02')
        household_member2 = HouseholdMember.objects.create(household=hhold, surname="name1", male=False, date_of_birth='1989-02-02')
        all_members = hhold.all_members()
        self.assertTrue(household_head in all_members)
        self.assertTrue(household_member1 in all_members)
        self.assertTrue(household_member2 in all_members)

    def test_should_know_if_all_members_have_completed_currently_open_batches(self):
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   location=kampala,
                                                   backend=backend)
        hhold = Household.objects.create(investigator=investigator, location=investigator.location, uid=0)
        household_head = HouseholdHead.objects.create(household=hhold,surname="Name", date_of_birth=date(1989, 2, 2))
        household_member1 = HouseholdMember.objects.create(household=hhold, surname="name2", male=False, date_of_birth=date(1989, 2, 2))
        household_member2 = HouseholdMember.objects.create(household=hhold, surname="name3", male=False, date_of_birth=date(1989, 2, 2))
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=2, condition="GREATER_THAN")
        condition.groups.add(member_group)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch_2 = Batch.objects.create(name="BATCH B", order=2)

        batch.open_for_location(investigator.location)

        question_1 = Question.objects.create(identifier="identifier1",
                                             text="Question 1", answer_type='number',
                                             order=1, subquestion=False, group=member_group)
        question_1.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)

        member_list = [household_head, household_member1, household_member2]

        self.assertFalse(hhold.completed_currently_open_batches())
        investigator.member_answered(question_1, household_member1, answer=1, batch=batch)
        self.assertFalse(hhold.completed_currently_open_batches())
        investigator.member_answered(question_1, household_member2, answer=1, batch=batch)
        self.assertFalse(hhold.completed_currently_open_batches())
        investigator.member_answered(question_1, household_head, answer=1, batch=batch)
        self.assertTrue(hhold.completed_currently_open_batches())
        self.assertEqual(3, HouseholdMemberBatchCompletion.objects.filter(batch=batch).count())
        [self.assertEqual(1, HouseholdMemberBatchCompletion.objects.filter(batch=batch, householdmember=member).count()) for member in member_list]

    def test_household_knows_survey_can_be_retaken(self):
        member_group = HouseholdMemberGroup.objects.create(name="Greater than 2 years", order=1)
        condition = GroupCondition.objects.create(attribute="AGE", value=3, condition="GREATER_THAN")
        condition.groups.add(member_group)
        backend = Backend.objects.create(name='something')
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="", mobile_number="123456789",
                                                   location=kampala,
                                                   backend=backend)

        household = Household.objects.create(investigator=investigator, uid=0)

        household_member = HouseholdMember.objects.create(surname="Member",
                                                          date_of_birth=date(1980, 2, 2), male=False, household=household)
        household_member_2 = HouseholdMember.objects.create(surname="Member 2",
                                                          date_of_birth=date(1980, 2, 2), male=False, household=household)
        batch = Batch.objects.create(name="BATCH A", order=1)
        batch_2 = Batch.objects.create(name="BATCH A", order=1)

        batch.open_for_location(investigator.location)
        batch_2.open_for_location(investigator.location)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
                                                investigator=investigator, household=household_member.household)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
                                                investigator=investigator, household=household_member.household)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
                                                investigator=investigator, household=household_member.household)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
                                                investigator=investigator, household=household_member.household)

        self.assertTrue(household.can_retake_survey(batch, 5))
        self.assertTrue(household.can_retake_survey(batch_2, 5))

        HouseholdMemberBatchCompletion.objects.all().delete()

        ten_minutes_ago = datetime.utcnow().replace(tzinfo=utc) - timedelta(minutes=10)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
                                                investigator=investigator, household=household_member.household,
                                                created=ten_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
                                                investigator=investigator, household=household_member.household,
                                                created=ten_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
                                                investigator=investigator, household=household_member.household)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
                                                investigator=investigator, household=household_member.household)
        self.assertFalse(household.can_retake_survey(batch, 5))
        self.assertTrue(household.can_retake_survey(batch_2, 5))

        HouseholdMemberBatchCompletion.objects.all().delete()

        three_minutes_ago = datetime.utcnow().replace(tzinfo=utc) - timedelta(minutes=3)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member,
                                                investigator=investigator, household=household_member.household,
                                                created=ten_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch, householdmember=household_member_2,
                                                investigator=investigator, household=household_member.household,
                                                created=three_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member,
                                                investigator=investigator, household=household_member.household,
                                                created=three_minutes_ago)

        HouseholdMemberBatchCompletion.objects.create(batch=batch_2, householdmember=household_member_2,
                                                investigator=investigator, household=household_member.household,
                                                created=ten_minutes_ago)
        self.assertTrue(household.can_retake_survey(batch, 5))
        self.assertTrue(household.can_retake_survey(batch_2, 5))

    def test_last_answered(self):
        self.batch = Batch.objects.create(order=1, name="Batch Name")
        self.another_batch = Batch.objects.create(order=2, name="Batch Name 2")

        self.batch.open_for_location(self.investigator.location)
        batch_question_1 = Question.objects.create(order=1, text="Test question 1",
                                                   answer_type=Question.NUMBER, group=self.member_group)
        question_2 = Question.objects.create(order=2, text="Test question 2",
                                answer_type=Question.NUMBER, group=self.member_group)
        batch_question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)

        BatchQuestionOrder.objects.create(question=batch_question_1, batch=self.batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=self.batch, order=2)

        self.investigator.member_answered(batch_question_1, self.household_member, 1, self.batch)
        self.assertEqual(batch_question_1.text, self.household_member.last_question_answered().text)

    def test_retake_latest_batch(self):
        batch_1 = Batch.objects.create(order=1)
        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_1.batches.add(batch_1)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch_1, order=1)

        batch_1.open_for_location(self.investigator.location)
        self.investigator.member_answered(question_1, self.household_member, 1, batch_1)
        batch_1.close_for_location(self.investigator.location)

        batch_2 = Batch.objects.create(order=2)

        question_2 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2.batches.add(batch_2)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch_2, order=1)

        batch_2.open_for_location(self.investigator.location)
        self.investigator.member_answered(question_2, self.household_member, 1, batch_2)

        self.assertEquals(NumericalAnswer.objects.count(), 2)

        self.household.retake_latest_batch()

        self.assertEquals(NumericalAnswer.objects.count(), 1)

    def test_has_pending_survey(self):
        batch = Batch.objects.create(order=1)
        batch.open_for_location(self.kampala)

        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_1.batches.add(batch)
        question_2.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)

        self.assertTrue(self.household.has_pending_survey())

        self.investigator.member_answered(question_1, self.household_member, 1, batch)

        self.assertTrue(self.household.has_pending_survey())

        self.investigator.member_answered(question_2, self.household_member, 1, batch)

        self.assertFalse(self.household.has_pending_survey())

    def test_knows_last_question_answered_by_household_and_household_has_next_question(self):
        batch = Batch.objects.create(order=1)
        batch.open_for_location(self.kampala)

        question_1 = Question.objects.create(text="How many members are there in this household?",
                                             answer_type=Question.NUMBER, order=1, group=self.member_group)
        question_2 = Question.objects.create(text="How many of them are male?",
                                             answer_type=Question.NUMBER, order=2, group=self.member_group)
        question_1.batches.add(batch)
        question_2.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)

        self.assertIsNone(self.household.last_question_answered())
        self.assertFalse(self.household.has_completed_batches([batch]))

        answers = self.household.answers_for([question_1, question_2])

        self.assertEqual('', answers[0])
        self.assertEqual('', answers[1])

        self.investigator.member_answered(question_1, self.household_member, 1, batch)

        self.assertEqual(question_1, self.household.last_question_answered())
        self.assertTrue(self.household.has_next_question(batch))
        self.assertFalse(self.household.survey_completed())

        self.investigator.member_answered(question_2, self.household_member, 1, batch)
        self.assertEqual(question_2, self.household.last_question_answered())
        self.assertFalse(self.household.has_next_question(batch))
        self.assertTrue(self.household.survey_completed())
        self.assertTrue(self.household.has_completed_batches([batch]))

    def test_knows_to_mark_answers_as_old(self):
        investigator = Investigator.objects.create(name="inv1", location=self.kampala,
                                                   backend=self.backend)
        household = Household.objects.create(investigator=investigator, location=self.kampala, uid=0)
        household_member = HouseholdMember.objects.create(surname='member1', date_of_birth=(date(2013, 8, 30)),
                                                          male=False,
                                                  household=household)

        batch = Batch.objects.create(name="Batch 1", order=1)
        group = HouseholdMemberGroup.objects.create(name="Group 1", order=1)
        group_condition = GroupCondition.objects.create(attribute="GENDER", condition="EQUALS", value=True)
        group_condition.groups.add(group)

        question_1 = Question.objects.create(group=group, text="This is another question", answer_type="number",
                                             order=1)
        question_1.batches.add(batch)
        BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)

        batch.open_for_location(investigator.location)
        investigator.member_answered(question_1, household_member, 1, batch)

        self.assertFalse(NumericalAnswer.objects.filter(question=question_1)[0].is_old)

        household.mark_past_answers_as_old()

        self.assertTrue(NumericalAnswer.objects.filter(question=question_1)[0].is_old)

    def test_should_know_total_households_in_location(self):
        open_survey = Survey.objects.create(name="open survey", description="open survey", has_sampling=True)
        Household.objects.all().delete()
        self.abim = Location.objects.create(name='Abim', tree_parent = self.uganda, type = self.city)
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent = self.kampala, type = self.city)

        investigator_1 = Investigator.objects.create(name='some_inv',mobile_number='123456783',male=True,location=self.kampala)
        investigator_2 = Investigator.objects.create(name='some_inv',mobile_number='123456781',male=True,location=self.kampala_city)

        household_1 = Household.objects.create(investigator = investigator_1,location= self.kampala, survey=open_survey)
        household_2 = Household.objects.create(investigator = investigator_2,location= self.kampala_city, survey=open_survey)

        self.assertEqual(2, Household.all_households_in(self.uganda, open_survey).count())
        self.assertIn(household_1, Household.all_households_in(self.uganda, open_survey))
        self.assertIn(household_2, Household.all_households_in(self.uganda, open_survey))

    def test_should_know_number_of_members_interviewed(self):
        self.batch = Batch.objects.create(name="BATCH A", order=1)
        Household.objects.all().delete()
        member_group = HouseholdMemberGroup.objects.create(name='group1',order=1)
        question = Question.objects.create(text="some question",answer_type=Question.NUMBER,order=1,group=member_group)
        self.batch.questions.add(question)
        BatchQuestionOrder.objects.create(question=question, batch=self.batch, order=1)

        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent = self.kampala, type = self.city)

        investigator_1 = Investigator.objects.create(name='some_inv',mobile_number='123456783',male=True,location=self.kampala)

        household_1 = Household.objects.create(investigator = investigator_1,location=self.kampala)
        member_1 = HouseholdMember.objects.create(household=household_1,date_of_birth=date(2000,02, 02))
        member_2 = HouseholdMember.objects.create(household=household_1,date_of_birth=date(2000,02, 02))
        member_3 = HouseholdMember.objects.create(household=household_1,date_of_birth=date(2000,02, 02))

        investigator_1.member_answered(question,member_1,1,self.batch)

        self.assertIn(member_1, household_1.members_interviewed(self.batch))

    def test_should_return_0_members_interviewed_if_no_question_in_batch(self):
        self.batch = Batch.objects.create(name="BATCH A", order=1)
        Household.objects.all().delete()
        self.kampala_city = Location.objects.create(name='Kampala City', tree_parent = self.kampala, type = self.city)

        investigator_1 = Investigator.objects.create(name='some_inv',mobile_number='123456783',male=True,location=self.kampala)

        household_1 = Household.objects.create(investigator = investigator_1,location=self.kampala)
        member_1 = HouseholdMember.objects.create(household=household_1,date_of_birth=datetime(2000,02, 02))
        member_2 = HouseholdMember.objects.create(household=household_1,date_of_birth=datetime(2000,02, 02))
        member_3 = HouseholdMember.objects.create(household=household_1,date_of_birth=datetime(2000,02, 02))

        self.assertEqual(0, len(household_1.members_interviewed(self.batch)))