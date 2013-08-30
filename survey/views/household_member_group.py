from django.http import HttpResponse
from django.shortcuts import render
from survey.models import GroupCondition, HouseholdMemberGroup

def conditions(request):
    conditions = GroupCondition.objects.all().order_by('condition')
    return render(request, 'household_member_groups/conditions.html', {'conditions': conditions, 'request': request})

def index(request):
    groups = HouseholdMemberGroup.objects.all().order_by('name')
    return render(request, 'household_member_groups/index.html', {'groups': groups, 'request': request})