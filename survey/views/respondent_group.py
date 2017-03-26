import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from survey.models import RespondentGroup, ParameterTemplate, RespondentGroupCondition
from survey.forms.respondent_group import GroupForm
from survey.utils.views_helper import contains_key
from survey.utils.query_helper import get_filterset


@permission_required('auth.can_view_interviewers')
def index(request):
    groups = RespondentGroup.objects.all()
    search_fields = ['name', 'description']
    if request.GET.has_key('q'):
        groups = get_filterset(groups, request.GET['q'], search_fields)
    return render(request, 'respondent_groups/index.html', {'groups': groups, 'request': request})


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


def _process_groupform(request, group_form, action):
    if group_form.is_valid():
        group = group_form.save()
        messages.success(request, 'Group successfully %s.' % action)
        return HttpResponseRedirect(reverse('respondent_groups_edit', args=(group.id,)))
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
            request, group_form, action='added')
    context = {'groups_form': group_form,
               'title': "New Group",
               'button_label': 'Create',
               'id': 'add_group_form',
               'action': reverse('new_respondent_groups_page'),
               'cancel_url': reverse('respondent_groups_page'),
               'parameter_questions': ParameterTemplate.objects.all(),
               'condition_title': "New Eligibility Criteria"}
    request.breadcrumbs([
        ('Member Groups', reverse('respondent_groups_page')),
    ])
    return response or render(request, 'respondent_groups/new.html', context)


@permission_required('auth.can_view_household_groups')
def edit_group(request, group_id):
    response = None
    group = RespondentGroup.objects.get(id=group_id)
    group_form = GroupForm(instance=group)
    if request.method == 'POST':
        group_form = GroupForm(request.POST, instance=group)
        performed_action = 'edited'
        response = _process_groupform(request, group_form, performed_action)
    context = {'groups_form': group_form,
               'title': "Edit Group",
               'button_label': 'Save',
               'id': 'add_group_form',
               'action': reverse('respondent_groups_edit', args=(group_id,)),
               'cancel_url': reverse('respondent_groups_page'),
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


@permission_required('auth.can_view_household_groups')
def delete_condition(request, condition_id):
  try:
    respondent_group_condition = RespondentGroupCondition.objects.filter(id=condition_id).values_list("respondent_group__id")
    respondent_group_condition[0][0]
    RespondentGroupCondition.objects.get(id=condition_id).delete()
  except Exception,err:
    print err
  messages.success(request, "Criteria successfully deleted.")
  # return HttpResponseRedirect("/conditions/")
  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
