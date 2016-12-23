import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from survey.models import RespondentGroup, ParameterTemplate, GroupCondition
from survey.forms.group_condition import GroupConditionForm
from survey.forms.respondent_group import GroupForm
from survey.forms.question_module_form import QuestionModuleForm
from survey.models.question_templates import QuestionTemplate
from survey.models import QuestionModule, Question
from survey.utils.views_helper import contains_key


@permission_required('auth.can_view_household_groups')
def conditions(request):
    conditions = GroupCondition.objects.all().order_by('condition')
    return render(request, 'respondent_groups/conditions/index.html',
                  {'conditions': conditions, 'add_condition_url': 'new_group_condition', 'request': request})


@permission_required('auth.can_view_interviewers')
def index(request):
    groups = RespondentGroup.objects.all()
    return render(request, 'respondent_groups/index.html', {'groups': groups, 'request': request})


def _get_conditions_hash():
    condition = GroupCondition.objects.all().latest('created')
    return {'id': condition.id,
            'value': "%s > %s > %s" % (condition.attribute, condition.condition, condition.value)}


@permission_required('auth.can_view_household_groups')
def add_condition(request):
    response = None
    condition_form = GroupConditionForm()

    if request.is_ajax():
        condition_form = GroupConditionForm(data=request.POST)
        _process_condition_form(request, condition_form)
        conditions = _get_conditions_hash()
        return HttpResponse(json.dumps(conditions), content_type='application/json')

    elif request.method == 'POST':
        condition_form = GroupConditionForm(data=request.POST)
        response = _process_condition_form(request, condition_form)
    context = {'button_label': 'Save',
               'title': 'New Criteria',
               'id': 'add-condition-form',
               'action': '/conditions/new/',
               'request': request,
               'condition_form': condition_form}

    return response or render(request, 'respondent_groups/conditions/new.html', context)


def has_valid_condition(data):
    if contains_key(data, 'conditions'):
        corresponding_condition = GroupCondition.objects.filter(
            id=int(data['conditions']))
        return corresponding_condition
    return False


def _process_condition_form(request, condition_form):
    if condition_form.is_valid():
        condition_form.save()
        messages.success(request, 'Condition successfully added.')
        redirect_url = '/conditions/'
    else:
        messages.error(request, 'Condition not added: %s' %
                       condition_form.non_field_errors()[0])
        redirect_url = '/conditions/new/'
    return HttpResponseRedirect(redirect_url)


def _process_groupform(request, group_form, action, redirect_url):
    if group_form.is_valid():
        group_form.save()
        messages.success(request, 'Group successfully %s.' % action)
        return HttpResponseRedirect(redirect_url)
    else:
        errors = group_form.non_field_errors()
        if errors:
            messages.error(request, 'Group not added: %s' % errors[0])


@permission_required('auth.can_view_household_groups')
def add_group(request):
    params = request.POST
    response = None
    group_form = GroupForm()

    if request.method == 'POST':
        group_form = GroupForm(params)
        response = _process_groupform(
            request, group_form, action='added', redirect_url=reverse('respondent_groups_page'))
    context = {'groups_form': group_form,
               'conditions': GroupCondition.objects.all(),
               'title': "New Group",
               'button_label': 'Create',
               'id': 'add_group_form',
               'action': reverse('new_respondent_groups_page'),
               'cancel_url': reverse('respondent_groups_page'),
               'condition_form': GroupConditionForm(),
               'parameter_questions': ParameterTemplate.objects.all(),
               'condition_title': "New Eligibility Criteria"}
    request.breadcrumbs([
        ('Member Groups', reverse('respondent_groups_page')),
    ])
    return response or render(request, 'respondent_groups/new.html', context)


@permission_required('auth.can_view_household_groups')
def details(request, group_id):
    group = RespondentGroup.objects.get(id=group_id)
    conditions = GroupCondition.objects.filter(groups__id=group_id)
    if not conditions.exists():
        messages.error(request, "No conditions in this group.")
        return HttpResponseRedirect("/groups/")
    return render(request, "household_member_groups/conditions/index.html",
                  {'conditions': conditions, 'add_condition_url': 'new_condition_for_group', 'group': group})


@permission_required('auth.can_view_household_groups')
def add_group_condition(request, group_id):
    condition_form = GroupConditionForm()
    if request.method == 'POST':
        condition_form = GroupConditionForm(data=request.POST)
        if condition_form.is_valid():
            try:
                group = RespondentGroup.objects.get(id=group_id)
                condition = condition_form.save()
                condition.groups.add(group)
                condition.save()
                messages.success(request, "Criteria successfully added.")
                redirect_url = '/groups/%s/' % group_id
            except ObjectDoesNotExist:
                messages.error(request, "Group does not exist.")
                redirect_url = '/groups/'
            return HttpResponseRedirect(redirect_url)

    context = {'button_label': 'Create',
               'title': 'New Criteria',
               'id': 'add-condition-to-group-form',
               'action': '/groups/%s/conditions/new/' % group_id,
               'request': request,
               'condition_form': condition_form}
    return render(request, 'respondent_groups/conditions/new.html', context)


@permission_required('auth.can_view_household_groups')
def edit_group(request, group_id):    
    response = None
    group = RespondentGroup.objects.get(id=group_id)
    group_form = GroupForm(instance=group)
    if request.method == 'POST':
        group_form = GroupForm(request.POST, instance=group)
        redirect_url = reverse('respondent_groups_edit', args=(group_id,))
        performed_action = 'edited'
        response = _process_groupform(
            request, group_form, performed_action, redirect_url)
    context = {'groups_form': group_form,
               'title': "Edit Group",
               'button_label': 'Save',
               'id': 'add_group_form',
               'action': reverse('respondent_groups_edit', args=(group_id,)),
               'cancel_url': reverse('respondent_groups_page'),
               'condition_form': GroupConditionForm(),
               'parameter_questions': ParameterTemplate.objects.all(),
               'condition_title': "New Eligibility Criteria"}
    request.breadcrumbs([
        ('Member Groups', reverse('respondent_groups_page')),
    ])
    return response or render(request, 'respondent_groups/new.html', context)


@permission_required('auth.can_view_household_groups')
def delete_group(request, group_id):    
    try:
        member_group = RespondentGroup.objects.get(id=group_id)
        print member_group, "membergroup"
        #member_group.remove_related_questions()
        member_group.delete()
        messages.success(request, "Group successfully deleted.")
    except Exception,err:
        print err
        messages.success(request, "Group does not exist.")
    return HttpResponseRedirect("/groups/")
    # member_group = RespondentGroup.objects.get(id=group_id)
    # if RespondentGroup.objects.filter(name=member_group).exists():
    #     messages.error(request, "Respondent Group cannot be deleted.")
    # else:
    #     member_group.delete()
    # return HttpResponseRedirect('/groups/')

@permission_required('auth.can_view_household_groups')
def delete_condition(request, condition_id):
    GroupCondition.objects.get(id=condition_id).delete()
    messages.success(request, "Criteria successfully deleted.")
    return HttpResponseRedirect("/conditions/")
