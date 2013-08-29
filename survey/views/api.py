from django.http import HttpResponse
from survey.models import Investigator, BatchLocationStatus, Household, HouseholdHead

def create_investigator(request):
    location = BatchLocationStatus.objects.all()[0].location
    investigator = Investigator.objects.create(name="Tester", mobile_number=request.GET['mobile_number'], location=location)
    household = Household.objects.create(investigator=investigator)
    HouseholdHead.objects.create(household=household, surname="Surname")
    return HttpResponse()

def delete_investigator(request):
    Investigator.objects.filter(mobile_number=request.GET['mobile_number']).delete()
    return HttpResponse()