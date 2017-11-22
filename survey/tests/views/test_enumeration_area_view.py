from model_mommy import mommy
from django.contrib.auth.models import User
from django.test import Client
from mock import patch
from survey.models.locations import *
from survey.models import Survey, EnumerationArea, Batch, BatchLocationStatus
from survey.tests.base_test import BaseTest
from survey.views.enumeration_area import _process_form
from django.utils.timezone import utc
from django.core.urlresolvers import reverse


class EAViewTest(BaseTest):

    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username='useless', email='rajni@kant.com', password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        self.client.login(username='Rajni', password='I_Rock')
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.uganda = Location.objects.create(name="Uganda", type=self.country)
        self.district_type = LocationType.objects.create(
            name="Districttype", slug='districttype', parent=self.country)
        self.county_type = LocationType.objects.create(
            name="Countytype", slug='countytype', parent=self.district_type)
        self.parish_type = LocationType.objects.create(
            name="Parishtype", slug='parishtype', parent=self.county_type)
        self.district = Location.objects.create(
            name="district1", parent=self.uganda, type=self.district_type)
        self.county_1 = Location.objects.create(
            name="county1", parent=self.district, type=self.county_type)
        self.parish_1 = Location.objects.create(
            name="parish_1", parent=self.county_1, type=self.parish_type)
        self.parish_1_b = Location.objects.create(
            name="parish_1b", parent=self.county_1, type=self.parish_type)
        self.district = Location.objects.create(
            name="district2", parent=self.uganda, type=self.district_type)
        self.county_2 = Location.objects.create(
            name="county2", parent=self.district, type=self.county_type)
        self.parish_2 = Location.objects.create(
            name="parish_2", parent=self.county_2, type=self.parish_type)
        self.ea = EnumerationArea.objects.create(name="EA1")
        self.ea.locations.add(self.parish_2)
        self.filedata = [
            ['Regiontype', 'Districttype', 'Counttype',
                'EA',                   'Parishtype', 'EA'],
            ['region1',    'district1',    'county1',
             'ea_containing_parish', 'parish_1',   ''],
            ['region1',    'district1',    'county1',
             'ea_containing_parish', 'parish_1b',  ''],
            ['region2',    'district2',    'county2',   '',
             'parish_2',    'ea_under_parish'],
            ['region2',    'district2',    'county2',   '',                     'parish_2',    'ea_under_parish']]
        self.filename = 'test_uganda.csv'
        self.write_to_csv('wb', self.filedata, self.filename)
        self.file = open(self.filename, 'rb')
        self.survey = Survey.objects.create(name="Survey")

    def test_new_ea(self):
        locations = Location.country().get_leafnodes(False)
        data = {'name': 'drishti', 'locations': list(locations.values_list('id', flat=True))}
        url = reverse('new_enumeration_area_page')
        response = self.client.post(url, data=data)
        self.assertEqual(302, response.status_code)
        self.assertTrue(EnumerationArea.objects.filter(name=data['name']).count(), 1)
        ea = EnumerationArea.objects.filter(name=data['name']).first()
        self.assertTrue(ea.locations.count(), len(locations))

    def test_create_new_ea_with_incomplete_params_does_not_create(self):
        data = {'name': 'drishti', }
        url = reverse('new_enumeration_area_page')
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        self.assertIn('Enumeration area was not created.', response.content)
        survey = mommy.make(Survey)
        survey2 = mommy.make(Survey, name='second')
        survey3 = mommy.make(Survey, name='third')
        batch1 = mommy.make(Batch, survey=survey)
        batch2 = mommy.make(Batch, survey=survey2)
        batch3 = mommy.make(Batch, survey=survey3)
        url = reverse('batch_open_page', args=(batch1.id, ))
        response = self.client.post(url, data={'location_id': Location.country().id})
        self.assertTrue(BatchLocationStatus.objects.filter(batch=batch1).count(), 1)
        url = reverse('batch_open_page', args=(batch2.id, ))
        response = self.client.post(url, data={'location_id': Location.country().id})
        self.assertTrue(BatchLocationStatus.objects.filter(batch=batch2).count(), 1)
        locations = Location.country().get_leafnodes(False)
        ea = mommy.make(EnumerationArea)
        for location in locations:
            ea.locations.add(location)
        url = reverse('open_surveys_in_ea_area')
        response = self.client.get(url, data={'ea_id': ea.id})

    def test_location_sub_types(self):
        url = reverse('location_sub_types')
        data = {'type': Location.country().type.id}
        import json
        response = json.loads(self.client.get(url, data=data).content)
        child_locations = Location.country().get_children()
        for location_data in response['locations']:
            self.assertTrue(child_locations.filter(id=location_data['id'], name=location_data['name']).count(), 1)

    def test_index_ea(self):
        response = self.client.get('/enumeration_area/')
        self.assertEqual(200, response.status_code)

    def test_filter_ea(self):
        response = self.client.get('/enumeration_area/filter/')
        self.assertEqual(200, response.status_code)

    def test_open_ea(self):        
        response = self.client.get(reverse('enumeration_area_filter'))
        self.assertEqual(200, response.status_code)
    
    def test_delete_ea(self):
        x= EnumerationArea.objects.create(name="tremp")
        response = self.client.get(reverse('delete_enumeration_area', kwargs={'ea_id': x.id}))        
        self.assertIn(response.status_code, [200,302])

    def test_edit_ea(self):
        locations = Location.country().get_leafnodes(False)
        ea = mommy.make(EnumerationArea)
        for location in locations:
            ea.locations.add(location)
        url = reverse('edit_enumeration_area_page', args=(ea.id, ))
        response = self.client.get(url)
        self.assertTrue(response.status_code, 200)
        data = {'name': 'EA edited', 'locations': list(locations.values_list('id', flat=True))[:1], }
        response = self.client.post(url, data)
        self.assertTrue(response.status_code, [200, 300])
        ea.refresh_from_db()
        self.assertTrue(ea.name, data['name'])


