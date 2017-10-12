import json
from django.test.client import Client
from survey.models.locations import *
from django.contrib.auth.models import User
from survey.tests.base_test import BaseTest
from django.core.urlresolvers import reverse

class LocationTest(BaseTest):

    def setUp(self):
        self.client = Client()
        self.client = Client()
        user_without_permission = User.objects.create_user(
            username='demo7', email='rajni@kant.com', password='demo7')
        self.client.login(username='demo7', password='demo7')
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.district = LocationType.objects.create(
            name='District', parent=self.country, slug='district')
        self.city = LocationType.objects.create(
            name='City', parent=self.district, slug='city')
        self.village = LocationType.objects.create(
            name='village', parent=self.city, slug='village')
        self.uganda = Location.objects.create(name='Uganda', type=self.country)
        self.kampala = Location.objects.create(
            name='Kampala', parent=self.uganda, type=self.district)
        self.kampala_city = Location.objects.create(
            name='Kampala City', parent=self.kampala, type=self.city)

    def test_get_children(self):
        LocationType.objects.create(name='Village', slug='village')
        country_obj = LocationType.objects.create(
            name='Country1', slug='country1')
        uganda_obj = Location.objects.create(name='locationsss_dd', type=country_obj)
        kampala = Location.objects.create(
            name='Kampala', parent=uganda_obj, type=self.city)
        abim = Location.objects.create(
            name='Abim', parent=uganda_obj, type=self.city)
        kampala_city = Location.objects.create(
            name='Kampala City', parent=kampala, type=self.village)
        content = json.loads(response.content)
        self.assertEquals(len(content), 2)
        self.assertEquals(content[0]['id'], abim.pk)
        self.assertEquals(content[0]['name'], abim.name)
        self.assertEquals(content[1]['id'], kampala.pk)
        self.assertEquals(content[1]['name'], kampala.name)

    def test_login_required(self):
        country_obj = LocationType.objects.create(
            name='Country2', slug='country2')
        uganda_obj = Location.objects.create(name='Ugandaddd', type=country_obj)
        self.assert_login_required(reverse('get_enumeration_areas',kwargs={'location_id':uganda_obj.id}))

    def test_view_location_list(self):
        uganda = Location.objects.create(name='Uganda', type=self.country)
        response = self.client.get(reverse('enumeration_area_home'))
        self.assertIn(response.status_code, [302,200])
        
    
    def test_add_location(self):
        response = self.client.get(reverse('new_enumeration_area_page'))
        self.assertIn(response.status_code, [302,200])
        templates = [template.name for template in response.templates]
        # # self.assertIn('enumeration_area_page/new.html', templates)
        # self.assertIsInstance(response.context['enumeration_area_form'], SurveyForm)
        # self.assertIn('Create', response.context['button_label'])
        # self.assertIn('New Enumeration Area', response.context['title'])
        # self.assertIn(reverse('new_enumeration_area_page'), response.context['action'])    
    
    # def test_should_throw_error_if_edit_non_existing_location(self):
    #     message = "Enumeration Area does not exist."
    #     self.assert_object_does_not_exist(reverse('edit_enumeration_area_page',kwargs={'ea_id':9999999944499}), message)

    # def test_should_throw_error_if_deleting_non_existing_location(self):
    #     message = "Enumeration Area does not exist."
    #     self.assert_object_does_not_exist(reverse('delete_enumeration_area_page',kwargs={'ea_id':9999994544999}), message)
