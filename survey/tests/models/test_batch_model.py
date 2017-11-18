from datetime import date, datetime
from django.test import TestCase
from survey.models.locations import LocationType, Location
from survey.models import HouseholdMemberGroup, LocationTypeDetails, GroupCondition, Backend, Interviewer, Household, Question, HouseholdMemberBatchCompletion, Batch, QuestionModule, EnumerationArea
# from survey.models.batch_question_order import BatchQuestionOrder
from survey.models.batch import Batch, BatchLocationStatus
from survey.models.households import HouseholdMember, HouseholdListing, SurveyHouseholdListing
from survey.models.surveys import Survey
from django.db import IntegrityError
from survey.models.questions import QuestionFlow


class BatchTest(TestCase):

    def test_fields(self):
        batch = Batch()
        fields = [str(item.attname) for item in batch._meta.fields]
        self.assertEqual(8, len(fields))
        for field in ['id', 'created', 'modified', 'order', 'name', 'description', 'survey_id', 'start_question_id']:
            self.assertIn(field, fields)

    def test_store(self):
        batch = Batch.objects.create(order=1, name="Batch name")
        self.failUnless(batch.id)

    def test_should_know_if_batch_is_open(self):
        batch = Batch.objects.create(order=1, name="Batch name")
        self.assertFalse(batch.is_open())
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(
            name='District', parent=country, slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, parent=uganda)
        batch.open_for_location(kampala)
        self.assertTrue(batch.is_open())

    def test_should_assign_order_as_0_if_it_is_the_only_batch(self):
        batch = Batch.objects.create(
            name="Batch name", description='description')
        batch = Batch.objects.get(name='Batch name')
        self.assertEqual(batch.order, 1)

    def test_should_assign_max_order_plus_one_if_not_the_only_batch(self):
        batch = Batch.objects.create(
            name="Batch name", description='description')
        batch_1 = Batch.objects.create(
            name="Batch name_1", description='description')
        batch_1 = Batch.objects.get(name='Batch name_1')
        self.assertEqual(batch_1.order, 2)

    def test_should_be_unique_together_batch_name_and_survey_id(self):
        survey = Survey.objects.create(name="very fast")
        batch_a = Batch.objects.create(
            survey=survey, name='Batch A', description='description')
        batch = Batch(survey=survey, name=batch_a.name,
                      description='something else')
        self.assertRaises(IntegrityError, batch.save)

    def test_knows_batch_is_complete_if_completion_object_exists_for_member(self):
        member_group = HouseholdMemberGroup.objects.create(
            name="Greater than 5 years", order=1)
        condition = GroupCondition.objects.create(
            attribute="AGE", value=5, condition="GREATER_THAN")
        condition.groups.add(member_group)
        backend = Backend.objects.create(name='something')
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        survey = Survey.objects.create(
            name="Survey A", description="open survey", has_sampling=True)
        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)

        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head",
                                             head_sex='MALE')

        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")

        another_household_member = HouseholdMember.objects.create(surname="sur123", first_name='fir123', gender='MALE', date_of_birth="1988-01-01",
                                                                  household=household, survey_listing=survey_householdlisting,
                                                                  registrar=investigator, registration_channel="ODK Access")
        batch = Batch.objects.create(order=1)

        batch.open_for_location(kampala)
        household_member_group = HouseholdMemberGroup.objects.create(
            name="Greater than 25 years", order=2)
        question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        batch = Batch.objects.create(order=1)
        question = Question.objects.create(identifier='1.1', text="This is a question", answer_type='Numerical Answer',
                                           group=household_member_group, batch=batch, module=question_mod)
        # question.batches.add(batch)
        # BatchQuestionOrder.objects.create(question=question, batch=batch, order=1)

        mem = HouseholdMemberBatchCompletion.objects.create(householdmember=household_member, batch=batch,
                                                            interviewer=investigator)
        self.assertEquals(mem.householdmember.surname, household_member.batch_completed(
            batch).householdmember.surname)

    # Eswar has_unanswered_question, members_answered
    # def test_knows_has_unanswered_questions_in_member_group(self):
    #     member_group = HouseholdMemberGroup.objects.create(name="Greater than 5 years", order=1)
    #     condition = GroupCondition.objects.create(attribute="AGE", value=5, condition="GREATER_THAN")
    #     condition.groups.add(member_group)
    #     backend = Backend.objects.create(name='something')
    #     country = LocationType.objects.create(name="Country", slug="country")
    #     city = LocationType.objects.create(name="City", slug="city")
    #     subcounty = LocationType.objects.create(name="Subcounty", slug="subcounty")
    #     parish = LocationType.objects.create(name="Parish", slug="parish")
    #     village = LocationType.objects.create(name="Village", slug="village")
    #     uganda = Location.objects.create(name="Uganda", type=country)
    #     kampala = Location.objects.create(name="Kampala",type=city, tree_parent=uganda)
    #     survey = Survey.objects.create(name="Survey A", description="open survey", has_sampling=True)
    #     ea = EnumerationArea.objects.create(name="EA2")
    #     ea.locations.add(kampala)
    #     investigator = Interviewer.objects.create(name="Investigator",
    #                                                ea=ea,
    #                                                gender='1',level_of_education='Primary',
    #                                                language='Eglish',weights=0)
    #
    #     household_listing = HouseholdListing.objects.create(ea=ea,list_registrar=investigator,initial_survey=survey)
    #     household = Household.objects.create(house_number=123456,listing=household_listing,physical_address='Test address',
    #                                          last_registrar=investigator,registration_channel="ODK Access",head_desc="Head",
    #                                          head_sex='MALE')
    #
    #     survey_householdlisting = SurveyHouseholdListing.objects.create(listing=household_listing,survey=survey)
    #     household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
    #                                                       household=household,survey_listing=survey_householdlisting,
    #                                                       registrar=investigator,registration_channel="ODK Access")
    #
    #     another_household_member = HouseholdMember.objects.create(surname="sur123", first_name='fir123', gender='MALE', date_of_birth="1988-01-01",
    #                                                       household=household,survey_listing=survey_householdlisting,
    #                                                       registrar=investigator,registration_channel="ODK Access")
    #     batch = Batch.objects.create(order=1)
    #     batch_2 = Batch.objects.create(name="BATCH A", order=2)
    #
    #     batch.open_for_location(kampala)
    #     batch_2.open_for_location(kampala)
    #
    #     household_member_group = HouseholdMemberGroup.objects.create(name="Greater than 25 years", order=2)
    #     question_mod = QuestionModule.objects.create(name="Test question name",description="test desc")
    #     batch = Batch.objects.create(order=1)
    #     question_1 = Question.objects.create(identifier='1.1',text="This is a question1", answer_type='Numerical Answer',
    #                                        group=household_member_group,batch=batch,module=question_mod)
    #     BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
    #
    #     question_2 = Question.objects.create(identifier='1.2',text="This is a question2", answer_type='Numerical Answer',
    #                                        group=household_member_group,batch=batch,module=question_mod)
    #
    #     BatchQuestionOrder.objects.create(question=question_2, batch=batch_2, order=1)
    #
    #     self.assertTrue(batch.has_unanswered_question(household_member))
    #     self.assertTrue(batch_2.has_unanswered_question(household_member))
    #
    #     investigator.member_answered(question_1, household_member, answer=2, batch=batch)
    #     self.assertFalse(batch.has_unanswered_question(household_member))
    #     self.assertTrue(batch_2.has_unanswered_question(household_member))
    #
    #     investigator.member_answered(question_2, household_member, answer=2, batch=batch_2)
    #     self.assertFalse(batch.has_unanswered_question(household_member))
    #     self.assertFalse(batch_2.has_unanswered_question(household_member))
    #
    #     self.assertFalse(batch.has_unanswered_question(another_household_member))
    #     self.assertFalse(batch_2.has_unanswered_question(another_household_member))

    def test_batch_knows_all_groups_it_has(self):
        batch = Batch.objects.create(
            name="Batch name", description='description')
        group_1 = HouseholdMemberGroup.objects.create(name="Group 1", order=0)
        group_2 = HouseholdMemberGroup.objects.create(name="Group 2", order=1)
        group_3 = HouseholdMemberGroup.objects.create(name="Group 3", order=2)
        household_member_group = HouseholdMemberGroup.objects.create(
            name="Greater than 65 years", order=10)
        question_mod = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        question_1 = Question.objects.create(identifier='1.1', text="This is a question1", answer_type='Numerical Answer',
                                             group=group_3, batch=batch, module=question_mod)

        question_2 = Question.objects.create(identifier='1.2', text="This is a question2", answer_type='Numerical Answer',
                                             group=group_1, batch=batch, module=question_mod)

        question_3 = Question.objects.create(identifier='1.3', text="This is a question3", answer_type='Numerical Answer',
                                             group=group_2, batch=batch, module=question_mod)

        # BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        # BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        # BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)

        batch_groups = [group_1, group_2, group_3]
        self.assertEqual(3, len(Question.objects.filter(batch=batch)))
        [self.assertIn(batch_group, Question.objects.filter(batch=batch).values_list('group__name'))
         for batch_group in Question.objects.filter(batch=batch).values_list('group__name')]

    # Eswar other_surveys_with_open_batches_in function need to be modified
    # def test_knows_open_batches_from_other_surveys_given_location(self):
    #     survey = Survey.objects.create(name="Test Survey1",description="Desc1",sample_size=10,has_sampling=True)
    #     another_survey = Survey.objects.create(name="Test Survey2",description="Desc2",sample_size=10,has_sampling=True)
    #     batch = Batch.objects.create(name="Batch name", description='description',order=11,survey=survey)
    #
    #     country = LocationType.objects.create(name="Country", slug="country")
    #     city = LocationType.objects.create(name="City", slug="city")
    #     subcounty = LocationType.objects.create(name="Subcounty", slug="subcounty")
    #     parish = LocationType.objects.create(name="Parish", slug="parish")
    #     village = LocationType.objects.create(name="Village", slug="village")
    #     uganda = Location.objects.create(name="Uganda", type=country)
    #     kampala = Location.objects.create(name="Kampala",type=city, tree_parent=uganda)
    #     # batch.open_for_location(kampala)
    #
    #     self.assertEqual(1, batch.other_surveys_with_open_batches_in(kampala))
    #     self.assertIn(another_survey, batch.other_surveys_with_open_batches_in(kampala))


class BatchLocationStatusTest(TestCase):

    def test_store(self):
        batch_1 = Batch.objects.create(order=1)
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        batch_location_status = BatchLocationStatus.objects.create(
            batch=batch_1, location=kampala)
        self.failUnless(batch_location_status.id)
        self.assertFalse(batch_location_status.non_response)

    def test_non_response_enabled(self):
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", parent=country, slug="city")
        subcounty = LocationType.objects.create(
            name="Subcounty", parent=city, slug="subcounty")
        parish = LocationType.objects.create(
            name="Parish", parent=subcounty, slug="parish")
        village = LocationType.objects.create(
            name="Village", parent=parish, slug="village")
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        ea = EnumerationArea.objects.create(name="open")
        ea.locations.add(kampala)
        survey = Survey.objects.create(
            name="Test Survey2222", description="Desc", sample_size=10, has_sampling=True)
        batch_123 = Batch.objects.create(order=1, name="123", survey=survey)
        self.assertFalse(batch_123.non_response_enabled(ea))

    # Eswar get_open_batch need to look for alternative
    def test_open_and_close_for_location(self):
        batch_1 = Batch.objects.create(order=1)
        batch_2 = Batch.objects.create(order=2)
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        abim = Location.objects.create(name="Abim", type=city, parent=uganda)
        # abim = Location.objects.create(name="Abim")
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        ea = EnumerationArea.objects.create(name="EA2")
        ea_2 = EnumerationArea.objects.create(name="EA12")
        ea.locations.add(kampala)
        ea_2.locations.add(abim)

        investigator_1 = Interviewer.objects.create(name="Investigator1             ",
                                                    ea=ea,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)
        investigator_2 = Interviewer.objects.create(name="Investigator2",
                                                    ea=ea_2,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)

        # self.assertEqual(len(investigator_1.get_open_batch()), 0)
        # self.assertEqual(len(investigator_2.get_open_batch()), 0)
        batch_1.open_for_location(kampala)
        batch_2.open_for_location(abim)

        self.assertTrue(batch_1.is_open())
        self.assertTrue(batch_2.is_open())
        batch_1.close_for_location(kampala)
        batch_2.close_for_location(abim)

        self.assertFalse(batch_1.is_open())
        self.assertFalse(batch_2.is_open())

    def test_get_next_question_from_batch(self):
        batch_1 = Batch.objects.create(order=1)
        batch_2 = Batch.objects.create(order=2)
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        abim = Location.objects.create(name="Abim", type=city, parent=uganda)
        group_1 = HouseholdMemberGroup.objects.create(
            name="test name", order=1)

        module = QuestionModule.objects.create(name="Education")

        question_1 = Question.objects.create(identifier='1.1', text="This is a question1", answer_type='Numerical Answer',
                                             group=group_1, batch=batch_1, module=module)

        question_2 = Question.objects.create(identifier='1.2', text="This is a question2", answer_type='Numerical Answer',
                                             group=group_1, batch=batch_2, module=module)

        question_3 = Question.objects.create(identifier='1.3', text="This is a question3", answer_type='Numerical Answer',
                                             group=group_1, batch=batch_1, module=module)
        # question_1.batches.add(batch)
        # question_2.batches.add(batch)
        # question_3.batches.add(batch_2)

        #
        batch_1.open_for_location(kampala)
        # self.assertIsNone(batch_1.get_next_open_batch(batch_1.order, kampala))
        #
        # batch_2.open_for_location(kampala)
        # self.assertEqual(batch_2, batch.get_next_open_batch(batch.order, kampala))

        # self.assertEqual(question_1, batch_1.next_inline_question(0, kampala))
        # self.assertEqual(question_2, batch_2.get_next_question(1, kampala))
        # self.assertEqual(question_3, batch_1.get_next_question(2, kampala))
        #
        # batch.close_for_location(kampala)
        # self.assertEqual(question_3, batch.get_next_question(0, kampala))

        self.assertFalse(batch_1.is_open_for(kampala))
        self.assertTrue(batch_2.open_for_location(abim))

    def test_knows_whether_can_be_deleted(self):
        batch = Batch.objects.create(order=2)
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        ea = EnumerationArea.objects.create(name="EA2")
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)

        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                household=household, survey_listing=survey_householdlisting,
                                                registrar=investigator, registration_channel="ODK Access")
        group = HouseholdMemberGroup.objects.create(name="test name", order=1)
        female = GroupCondition.objects.create(
            attribute="gender", value=True, condition="EQUALS")
        group.conditions.add(female)
        module = QuestionModule.objects.create(
            name="Test question name", description="test desc")
        question_1 = Question.objects.create(identifier='1.1', text="This is a question1", answer_type='Numerical Answer',
                                             group=group, batch=batch, module=module)

        question_2 = Question.objects.create(identifier='1.2', text="This is a question2", answer_type='Numerical Answer',
                                             group=group, batch=batch, module=module)

        question_3 = Question.objects.create(identifier='1.3', text="This is a question3", answer_type='Numerical Answer',
                                             group=group, batch=batch, module=module)
        # BatchQuestionOrder.objects.create(question=question_1, batch=batch, order=1)
        # BatchQuestionOrder.objects.create(question=question_2, batch=batch, order=2)
        # BatchQuestionOrder.objects.create(question=question_3, batch=batch, order=3)

        batch.open_for_location(kampala)
        # investigator.member_answered(question_1, member, 1, batch)
        # investigator.member_answered(question_2, member, 1, batch)
        # investigator.member_answered(question_3, member, 1, batch)
        batch.close_for_location(kampala)
        can_delete_batch, message = batch.can_be_deleted()
        self.assertTrue(can_delete_batch)
        self.assertEqual(message, '')

    def test_activate_non_response_for_location(self):
        batch = Batch.objects.create(order=1)
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        abim = Location.objects.create(name="Abim", type=city, parent=uganda)
        bukoto = Location.objects.create(
            name="Bukoto", type=subcounty, parent=kampala)
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        investigator_1 = Interviewer.objects.create(name="Investigator1",
                                                    ea=ea,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)
        investigator_2 = Interviewer.objects.create(name="Investigator2",
                                                    ea=ea,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)

        # self.assertEqual(len(investigator_1.get_open_batch()), 0)
        # self.assertEqual(len(investigator_2.get_open_batch()), 0)
        self.assertIsNone(batch.activate_non_response_for(kampala))

        batch.open_for_location(kampala)
        batch.activate_non_response_for(kampala)

        self.assertEqual(1, batch.open_locations.filter(
            non_response=True, location=kampala).count())
        self.assertEqual(0, batch.open_locations.filter(
            non_response=True, location=bukoto).count())

    def test_de_activate_non_response_for_location(self):
        batch = Batch.objects.create(order=1)
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        abim = Location.objects.create(name="Abim", type=city, parent=uganda)
        bukoto = Location.objects.create(
            name="Bukoto", type=subcounty, parent=kampala)
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        investigator_1 = Interviewer.objects.create(name="Investigator1",
                                                    ea=ea,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)
        investigator_2 = Interviewer.objects.create(name="Investigator2",
                                                    ea=ea,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)
        #
        # self.assertEqual(len(investigator_1.get_open_batch()), 0)
        # self.assertEqual(len(investigator_2.get_open_batch()), 0)

        batch.open_for_location(kampala)
        batch.activate_non_response_for(kampala)

        batch.deactivate_non_response_for(kampala)

        self.assertEqual(0, batch.open_locations.filter(
            non_response=True, location=kampala).count())
        self.assertEqual(0, batch.open_locations.filter(
            non_response=True, location=bukoto).count())
        self.assertEqual(1, batch.open_locations.filter(
            non_response=False, location=kampala).count())
        self.assertEqual(0, batch.open_locations.filter(
            non_response=False, location=bukoto).count())

    def test_knows_is_non_response_is_activate_for_location(self):
        batch = Batch.objects.create(order=1)
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        abim = Location.objects.create(name="Abim", type=city, parent=uganda)
        bukoto = Location.objects.create(
            name="Bukoto", type=subcounty, parent=kampala)
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        ea_2 = EnumerationArea.objects.create(name="Kampala EA A")
        ea_2.locations.add(abim)
        investigator_1 = Interviewer.objects.create(name="Investigator1",
                                                    ea=ea,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)
        investigator_2 = Interviewer.objects.create(name="Investigator2",
                                                    ea=ea_2,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)
        batch.open_for_location(kampala)
        batch.activate_non_response_for(kampala)
#        self.assertEquals(bukoto, list(batch.get_non_response_active_locations())[0])

        batch.deactivate_non_response_for(kampala)
        self.assertEquals(
            0, len(list(batch.get_non_response_active_locations())))

    def test_gets_all_locations_for_which_non_response_is_active(self):
        batch = Batch.objects.create(order=1)
        country = LocationType.objects.create(name="Country", slug="country")
        city = LocationType.objects.create(
            name="City", slug="city", parent=country)
        subcounty = LocationType.objects.create(
            name="Subcounty", slug="subcounty", parent=city)
        parish = LocationType.objects.create(
            name="Parish", slug="parish", parent=subcounty)
        village = LocationType.objects.create(
            name="Village", slug="village", parent=parish)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=city, parent=uganda)
        abim = Location.objects.create(name="Abim", type=city, parent=uganda)
        bukoto = Location.objects.create(
            name="Bukoto", type=subcounty, parent=kampala)
        batch.open_for_location(abim)
        batch.activate_non_response_for(abim)
        self.assertIn(abim, batch.get_non_response_active_locations())
        # [self.assertNotIn(location, list(batch.get_non_response_active_locations())) for location in [bukoto, kampala]]


class HouseholdBatchCompletionTest(TestCase):

    def test_store(self):
        batch = Batch.objects.create(order=1)
        country = LocationType.objects.create(name="Country", slug="country")
        district = LocationType.objects.create(
            name="District", slug="district", parent=country)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, parent=uganda)
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name="Investigator1",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Survey A", description="open survey", has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head",
                                             head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")
        batch_completion = HouseholdMemberBatchCompletion.objects.create(householdmember=household_member, batch=batch,
                                                                         interviewer=investigator)
        self.failUnless(batch_completion.id)
#

    def test_completed(self):
        batch = Batch.objects.create(order=1)
        country = LocationType.objects.create(name="Country", slug="country")
        district = LocationType.objects.create(
            name="District", slug="district", parent=country)
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, parent=uganda)
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name="Investigator1",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Survey A", description="open survey", has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head",
                                             head_sex='MALE')
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household_member = HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                          household=household, survey_listing=survey_householdlisting,
                                                          registrar=investigator, registration_channel="ODK Access")

        self.assertFalse(household.has_completed_batch(batch))

        household.batch_completed(batch, investigator)
        household_member.batch_completed(batch)

        self.assertTrue(household.has_completed_batch(batch))
