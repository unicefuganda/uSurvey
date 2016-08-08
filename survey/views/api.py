from django.http import HttpResponse
from survey.models import EnumerationArea
from survey.models.batch import BatchLocationStatus
from survey.models.households import HouseholdHead, Household
from survey.models import Interviewer


def create_interviewer(request):
    location = BatchLocationStatus.objects.all()[0].location
    ea = EnumerationArea.objects.create(name="EA2")
    ea.locations.add(location)

    interviewer = Interviewer.objects.create(name="Tester", mobile_number=request.GET['mobile_number'], ea=ea)
    household = Household.objects.create(interviewer=interviewer, uid=0)
    HouseholdHead.objects.create(household=household, surname="Surname", date_of_birth='1980-09-01')
    return HttpResponse()

def delete_interviewer(request):
    interviewer.objects.filter(mobile_number=request.GET['mobile_number']).delete()
    return HttpResponse()