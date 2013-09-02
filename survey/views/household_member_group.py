from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from survey.models import GroupCondition, HouseholdMemberGroup
from survey.forms.group_condition import GroupConditionForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

def conditions(request):
    conditions = GroupCondition.objects.all().order_by('condition')
    return render(request, 'household_member_groups/conditions/index.html', {'conditions': conditions, 'request': request})

def index(request):
    groups = HouseholdMemberGroup.objects.all().order_by('order')
    return render(request, 'household_member_groups/index.html', {'groups': groups, 'request': request})

@permission_required('auth.can_view_batches')
def add_condition(request):
    response = None
    condition_form = GroupConditionForm() 
    if request.method == 'POST':
        condition_form = GroupConditionForm(data=request.POST)
        if condition_form.is_valid():
            condition_form.save()
            messages.success(request, 'Condition successfully added.')
            response = HttpResponseRedirect("/conditions/")

    context = { 'button_label':'Save',
                'title': 'New condition', 
                'id':'add-condition-form',
                'action': '/conditions/new/',
                'request':request,
                'condition_form' : condition_form }
    return response or render(request, 'household_member_groups/conditions/new.html', context)