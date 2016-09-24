from django.test import TestCase
from survey.models.locations import Location, LocationType
from survey.forms.surveys import SurveyForm
from survey.models import Batch, Interviewer, SurveyAllocation, Backend, Household, HouseholdHead, \
    HouseholdMemberBatchCompletion, EnumerationArea, Question, HouseholdMemberGroup, QuestionModule
from survey.models.households import HouseholdMember, HouseholdListing, SurveyHouseholdListing
from survey.models.surveys import Survey


class SurveyTest(TestCase):

    def test_fields(self):
        survey = Survey()
        fields = [str(item.attname) for item in survey._meta.fields]
        self.assertEqual(8, len(fields))
        for field in ['id', 'created', 'modified', 'name', 'description', 'sample_size', 'has_sampling', 'preferred_listing_id']:
            self.assertIn(field, fields)

    def test_store(self):
        survey = Survey.objects.create(
            name="survey name", description="rajni survey")
        self.failUnless(survey.id)
        self.failUnless(survey.id)
        self.failUnless(survey.created)
        self.failUnless(survey.modified)
        self.assertEquals(10, survey.sample_size)
        self.assertTrue(survey.has_sampling)

    def test_survey_knows_it_is_open(self):
        survey = Survey.objects.create(
            name="survey name", description="rajni survey")
        batch = Batch.objects.create(order=1)
        ea = EnumerationArea.objects.create(name="EA2")
        country = LocationType.objects.create(name="Country", slug="country")
        region = LocationType.objects.create(name="Region", slug="region")
        district = LocationType.objects.create(
            name="District", slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", tree_parent=uganda, type=district)
        ea.locations.add(kampala)

        self.investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)

        survey = Survey.objects.create(
            name="survey name123", description="rajni survey123")
        batch = Batch.objects.create(order=1, survey=survey)

        batch.open_for_location(kampala)

        self.assertTrue(survey.is_open())

    def test_survey_knows_it_is_open_for_investigator_location_if_provided(self):
        survey = Survey.objects.create(
            name="survey name234", description="rajni surve234y")
        ea = EnumerationArea.objects.create(name="EA2")
        country = LocationType.objects.create(name="Country", slug="country")
        region = LocationType.objects.create(name="Region", slug="region")
        district = LocationType.objects.create(
            name="District", slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", tree_parent=uganda, type=district)
        ea.locations.add(kampala)

        self.investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)

        survey = Survey.objects.create(
            name="survey name333", description="rajni survey33333")
        batch = Batch.objects.create(order=1, survey=survey)
        survey_allocation = SurveyAllocation.objects.create(interviewer=self.investigator, survey=survey, allocation_ea=ea, stage=2,
                                                            status=0)
        batch.open_for_location(kampala)
        self.assertTrue(survey.is_open())

    def test_survey_knows_it_is_not_open_for_investigator_location_if_provided(self):
        survey = Survey.objects.create(
            name="survey name234", description="rajni surve234y")
        ea = EnumerationArea.objects.create(name="EA2")
        country = LocationType.objects.create(name="Country", slug="country")
        region = LocationType.objects.create(name="Region", slug="region")
        district = LocationType.objects.create(
            name="District", slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", tree_parent=uganda, type=district)
        ea.locations.add(kampala)

        self.investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)

        survey = Survey.objects.create(
            name="survey name333", description="rajni survey33333")
        batch = Batch.objects.create(order=1, survey=survey)
        survey_allocation = SurveyAllocation.objects.create(interviewer=self.investigator, survey=survey, allocation_ea=ea, stage=2,
                                                            status=0)
        self.assertFalse(survey.is_open())

    def test_survey_knows_it_is_closed(self):
        survey = Survey.objects.create(
            name="survey name closed", description="closed")
        ea = EnumerationArea.objects.create(name="EA23")
        country = LocationType.objects.create(name="Country", slug="country")
        region = LocationType.objects.create(name="Region", slug="region")
        district = LocationType.objects.create(
            name="District", slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", tree_parent=uganda, type=district)
        ea.locations.add(kampala)

        self.investigator = Interviewer.objects.create(name="Investigator_closed",
                                                       ea=ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)

        survey = Survey.objects.create(
            name="survey name up for close", description="rajni survey close")
        batch = Batch.objects.create(order=1, survey=survey)
        survey_allocation = SurveyAllocation.objects.create(interviewer=self.investigator, survey=survey, allocation_ea=ea, stage=2,
                                                            status=0)
        self.assertFalse(survey.is_open())

    def test_saves_survey_with_sample_size_from_form_if_has_sampling_is_true(self):
        form_data = {
            'name': 'survey rajni',
            'description': 'survey description rajni',
            'has_sampling': True,
            'sample_size': 10,
            'type': True,
        }
        survey_form = SurveyForm(data=form_data)
        Survey.save_sample_size(survey_form)
        saved_survey = Survey.objects.filter(
            name=form_data['name'], has_sampling=form_data['has_sampling'])
        self.failUnless(saved_survey)
        self.assertEqual(form_data['sample_size'], saved_survey[0].sample_size)

    def test_saves_survey_with_sample_size_zero_if_has_sampling_is_false(self):
        form_data = {
            'name': 'survey rajni',
            'description': 'survey description rajni',
            'has_sampling': False,
            'sample_size': 10,
            'type': True,
        }
        survey_form = SurveyForm(data=form_data)
        Survey.save_sample_size(survey_form)
        saved_survey = Survey.objects.filter(
            name=form_data['name'], has_sampling=form_data['has_sampling'])
        self.failUnless(saved_survey)
        self.assertEqual(0, saved_survey[0].sample_size)

    def test_unicode_text(self):
        survey = Survey.objects.create(
            name="survey name", description="rajni survey")
        self.assertEqual(survey.name, str(survey))

    def test_knows_currently_open_survey(self):
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(
            name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, tree_parent=uganda)

        open_survey = Survey.objects.create(
            name="open survey", description="open survey")
        closed_survey = Survey.objects.create(
            name="closed survey", description="closed survey")
        another_closed_survey = Survey.objects.create(
            name="another closed survey", description="another closed survey")

        open_batch = Batch.objects.create(
            order=1, name="Open Batch", survey=open_survey)
        closed_batch = Batch.objects.create(
            order=2, name="Closed Batch", survey=closed_survey)
        another_closed_batch = Batch.objects.create(
            order=3, name="Another Closed Batch", survey=another_closed_survey)

        open_batch.open_for_location(kampala)
        self.assertTrue(open_survey.is_open())
        self.assertFalse(closed_survey.is_open())

    def test_returns_none_if_there_is_no_currently_open_survey(self):
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(
            name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, tree_parent=uganda)

        open_survey = Survey.objects.create(
            name="open survey", description="open survey")
        closed_survey = Survey.objects.create(
            name="closed survey", description="closed survey")
        another_closed_survey = Survey.objects.create(
            name="another closed survey", description="another closed survey")

        open_batch = Batch.objects.create(
            order=1, name="Open Batch", survey=open_survey)
        closed_batch = Batch.objects.create(
            order=2, name="Closed Batch", survey=closed_survey)
        another_closed_batch = Batch.objects.create(
            order=3, name="Another Closed Batch", survey=another_closed_survey)

        self.assertFalse(None, open_batch.open_for_location(kampala)[1])

    def test__survey_knows_is_currently_open_for_location(self):
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(
            name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, tree_parent=uganda)
        masaka = Location.objects.create(
            name="masaka", type=district, tree_parent=uganda)
        wakiso = Location.objects.create(
            name="wakiso", type=district, tree_parent=uganda)

        open_survey = Survey.objects.create(
            name="open survey", description="open survey")

        open_batch = Batch.objects.create(
            order=1, name="Open Batch", survey=open_survey)
        open_batch_2 = Batch.objects.create(
            order=2, name="Open Batch 2", survey=open_survey)
        open_batch.open_for_location(kampala)
        open_batch_2.open_for_location(masaka)
        self.assertTrue(open_survey.is_open_for(kampala))
        self.assertTrue(open_survey.is_open_for(masaka))
        self.assertFalse(open_survey.is_open_for(wakiso))

    def test_survey_knows_count_of_respondents_in_a_location(self):
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(
            name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(
            name="Kampala", type=district, tree_parent=uganda)

        survey = Survey.objects.create(
            name="open survey", description="open survey", has_sampling=True)
        backend = Backend.objects.create(name='something')

        ea = EnumerationArea.objects.create(name="EA2")
        ea.locations.add(kampala)

        investigator = Interviewer.objects.create(name="Investigator1",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)

        investigator_2 = Interviewer.objects.create(name="Investigator2",
                                                    ea=ea,
                                                    gender='1', level_of_education='Primary',
                                                    language='Eglish', weights=0)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        survey_householdlisting = SurveyHouseholdListing.objects.create(
            listing=household_listing, survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head",
                                             head_sex='MALE')
        household_head = HouseholdHead.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                                      household=household, survey_listing=survey_householdlisting,
                                                      registrar=investigator, registration_channel="ODK Access",
                                                      occupation="Agricultural labor", level_of_education="Primary",
                                                      resident_since='1989-02-02')
        HouseholdMember.objects.create(surname="sur", first_name='fir', gender='MALE', date_of_birth="1988-01-01",
                                       household=household, survey_listing=survey_householdlisting,
                                       registrar=investigator, registration_channel="ODK Access")

        household_2 = Household.objects.create(house_number=1234567, listing=household_listing, physical_address='Test address7',
                                               last_registrar=investigator, registration_channel="ODK Access", head_desc="Head",
                                               head_sex='MALE')
        household_head_2 = HouseholdHead.objects.create(surname="sur2", first_name='fir2', gender='FEMALE', date_of_birth="1981-01-01",
                                                        household=household_2, survey_listing=survey_householdlisting,
                                                        registrar=investigator, registration_channel="USSD Access",
                                                        occupation="Others", level_of_education="Primary",
                                                        resident_since='1989-02-02')
        batch = Batch.objects.create(order=1, survey=survey)
        HouseholdMemberBatchCompletion.objects.create(householdmember=household_head, batch=batch,
                                                      interviewer=investigator)
        HouseholdMemberBatchCompletion.objects.create(householdmember=household_head_2, batch=batch,
                                                      interviewer=investigator_2)
        household_2.batch_completed(batch, investigator)
        self.assertEqual(1, len(survey.generate_completion_report(batch)))
