# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from django.test import TestCase
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import LocationAutoComplete


class LocationTest(TestCase):
    def test_store(self):
        country = LocationType.objects.create(name='Country', slug='country')
        district = LocationType.objects.create(name='District', slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)

        u = Location.objects.get(type__name='Country', name='Uganda')
        report_locations = u.get_descendants(include_self=True).all()
        self.assertEqual(len(report_locations), 2)
        self.assertIn(uganda, report_locations)
        self.assertIn(kampala, report_locations)


class LocationAutoCompleteTest(TestCase):
    def test_store(self):
        self.assertEqual(len(LocationAutoComplete.objects.all()), 0)
        uganda = Location.objects.create(name="Uganda")
        self.assertEqual(len(LocationAutoComplete.objects.all()), 1)
        self.assertEqual(uganda.auto_complete_text(), "Uganda")
        self.assertEqual(LocationAutoComplete.objects.all()[0].text, "Uganda")

        kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
        self.assertEqual(kampala.auto_complete_text(), "Uganda > Kampala")

        soroti = Location.objects.create(name="Soroti", tree_parent=kampala)
        self.assertEqual(soroti.auto_complete_text(), "Uganda > Kampala > Soroti")

        kampala.name = "Kampala Changed"
        kampala.save()
        self.assertEqual(kampala.auto_complete_text(), "Uganda > Kampala Changed")

        soroti = Location.objects.get(name="Soroti")
        self.assertEqual(soroti.auto_complete_text(), "Uganda > Kampala Changed > Soroti")