import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from survey.models import GroupCondition, HouseholdMemberGroup
from survey.forms.group_condition import GroupConditionForm
from survey.forms.group_condition_mapping import GroupConditionMappingForm
from survey.forms.household_member_group import HouseholdMemberGroupForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from survey.views.views_helper import contains_key


@permission_required('auth.can_view_investigators')
def conditions(request):
    conditions = GroupCondition.objects.all().order_by('condition')
    return render(request, 'household_member_groups/conditions/index.html',
                  {'conditions': conditions, 'request': request})


@permission_required('auth.can_view_investigators')
def index(request):
    groups = HouseholdMemberGroup.objects.all().order_by('order')
    return render(request, 'household_member_groups/index.html', {'groups': groups, 'request': request})


def _get_conditions_hash():
    condition = GroupCondition.objects.all().latest('created')
    return {'id': condition.id,
            'value': "%s > %s > %s" % (condition.attribute, condition.condition, condition.value)}


@permission_required('auth.can_view_batches')
def add_condition(request):
    response = None
    condition_form = GroupConditionForm()

    if request.is_ajax():
        _process_condition_form(request)
        conditions = _get_conditions_hash()
        return HttpResponse(json.dumps(conditions), mimetype='application/json')

    elif request.method == 'POST':
        _process_condition_form(request)
        response = HttpResponseRedirect("/conditions/")

    context = {'button_label': 'Save',
               'title': 'New condition',
               'id': 'add-condition-form',
               'action': '/conditions/new/',
               'request': request,
               'condition_form': condition_form}
    return response or render(request, 'household_member_groups/conditions/new.html', context)


def has_valid_condition(data):
    if contains_key(data, 'condition'):
        corresponding_condition = GroupCondition.objects.filter(id=int(data['condition']))
        return corresponding_condition
    return False


def _process_condition_form(request):
    condition_form = GroupConditionForm(data=request.POST)
    if condition_form.is_valid():
        condition_form.save()
        messages.success(request, 'Condition successfully added.')


def _process_groupform(request, group_form):
    if group_form.is_valid() and has_valid_condition(request.POST):
        group = group_form.save()
        params = dict(request.POST)
        for condition in params['condition']:
            group_mapping_form = GroupConditionMappingForm(
                {'household_member_group': group.id, 'group_condition':condition })
            group_mapping_form.save()
        messages.success(request, 'Group successfully added.')
        return HttpResponseRedirect("/groups/")


def add_group(request):
    response = None
    if request.method == 'POST':
        group_form = HouseholdMemberGroupForm(data=request.POST)
        response = _process_groupform(request, group_form)
    context = {'groups_form': HouseholdMemberGroupForm(),
               'conditions': GroupCondition.objects.all(),
               'title': "New Group",
               'button_label': 'Save',
               'id': 'add_group_form',
               'action': "/groups/new/",
               'condition_form': GroupConditionForm(),
               'condition_title': "New Condition"}

    return response or render(request, 'household_member_groups/new.html', context)