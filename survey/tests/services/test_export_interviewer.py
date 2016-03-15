# __author__ = 'administrator'
#
# from survey.models import Backend, Household, LocationTypeDetails, EnumerationArea
# from survey.models.locations import *
# from survey.models.interviewer import Interviewer
# from django.conf import settings
# from survey.tests.base_test import BaseTest
#
# from survey.forms.interviewer import InterviewerForm
# from survey.services.export_interviewers import *
#
# class EAUploadTest(BaseTest):
#     def test_download_interviewer(self):
#         self.country = LocationType.objects.create(name='Country', slug='country')
#         self.district = LocationType.objects.create(name='District', slug='district',parent=self.country)
#         self.city = LocationType.objects.create(name='City', slug='city', parent=self.district)
#         self.village = LocationType.objects.create(name='Village', slug='village',parent=self.city)
#
#         self.uganda = Location.objects.create(name='Uganda', type=self.country)
#         LocationTypeDetails.objects.create(country=self.uganda, location_type=self.country)
#         LocationTypeDetails.objects.create(country=self.uganda, location_type=self.district)
#         LocationTypeDetails.objects.create(country=self.uganda, location_type=self.city)
#         LocationTypeDetails.objects.create(country=self.uganda, location_type=self.village)
#
#         self.kampala = Location.objects.create(name='Kampala', parent=self.uganda, type=self.district)
#         self.abim = Location.objects.create(name='Abim', parent=self.uganda, type=self.district)
#         self.kampala_city = Location.objects.create(name='Kampala City', parent=self.kampala, type=self.city)
#         ea = EnumerationArea.objects.create(name="Kampala EA A")
#         ea.locations.add(self.kampala)
#         #ea.locations.add(kampala)
#         investigator = Interviewer.objects.create(name="Investigator",
#                                                    ea=ea,
#                                                    gender='1',level_of_education='Primary',
#                                                    language='Eglish',weights=0)
#         interviwer=ExportInterviewersService([u'DISTRICT', u'CITY', 'EA', 'NAME', 'AGE', 'LEVEL_OF_EDUCATION', 'LANGUAGE', 'MOBILE_NUMBERS', 'ODK_ID']).formatted_responses()
#         print interviwer,"int"
#
