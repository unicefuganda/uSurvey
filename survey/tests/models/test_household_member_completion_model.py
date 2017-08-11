from django.test import TestCase
from survey.models import Batch, Interviewer, Backend, Household, Survey, LocationTypeDetails
from survey.models.household_batch_completion import HouseholdBatchCompletion
from survey.models.locations import Location, LocationType
from survey.models import EnumerationArea
from survey.models.households import Household, HouseholdListing, HouseholdMember, SurveyHouseholdListing


class HouseholdMemberBatchCompletionTest(TestCase):

    def test_fields(self):
        member_completion = HouseholdBatchCompletion()
        fields = [str(item.attname) for item in member_completion._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created', 'modified', 'household_id', 'interviewer_id', 'batch_id']:
            self.assertIn(field, fields)

    def test_store(self):
        batch = Batch.objects.create(order=1)
        country = LocationType.objects.create(name="Country", slug="country")
        region = LocationType.objects.create(name="Region", slug="region")
        district = LocationType.objects.create(
            name="District", slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        central = Location.objects.create(
            name="CENTRAL", type=region, tree_parent=uganda)
        kampala = Location.objects.create(
            name="Kampala", tree_parent=central, type=district)

        # kampala = Location.objects.create(name="Kampala")
        ea = EnumerationArea.objects.create(name="Kampala EA A")
        # ea.locations.add(kampala)
        investigator = Interviewer.objects.create(name="Investigator",
                                                  ea=ea,
                                                  gender='1', level_of_education='Primary',
                                                  language='Eglish', weights=0)
        survey = Survey.objects.create(
            name="Test Survey", description="Desc", sample_size=10, has_sampling=True)
        household_listing = HouseholdListing.objects.create(
            ea=ea, list_registrar=investigator, initial_survey=survey)
        household = Household.objects.create(house_number=123456, listing=household_listing, physical_address='Test address',
                                             last_registrar=investigator, registration_channel="ODK Access", head_desc="Head", head_sex='MALE')

        batch_completion = HouseholdBatchCompletion.objects.create(
            household=household, interviewer=investigator, batch=batch)
        self.failUnless(batch_completion.id)
