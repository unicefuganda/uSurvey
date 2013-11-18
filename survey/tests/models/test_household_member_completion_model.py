from django.test import TestCase
from rapidsms.contrib.locations.models import Location
from survey.models import Batch, Investigator, Backend, Household
from survey.models.household_batch_completion import HouseholdBatchCompletion


class HouseholdMemberBatchCompletionTest(TestCase):
    def test_fields(self):
        member_completion = HouseholdBatchCompletion()
        fields = [str(item.attname) for item in member_completion._meta.fields]
        self.assertEqual(6, len(fields))
        for field in ['id', 'created', 'modified', 'household_id', 'investigator_id', 'batch_id']:
            self.assertIn(field, fields)

    def test_store(self):
        batch = Batch.objects.create(order=1)
        kampala = Location.objects.create(name="Kampala")
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=kampala,
                                                   backend=Backend.objects.create(name='something'))
        household = Household.objects.create(investigator=investigator, uid=0)

        batch_completion = HouseholdBatchCompletion.objects.create(household=household, investigator=investigator, batch=batch)
        self.failUnless(batch_completion.id)