from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from survey.forms.householdMember import HouseholdMemberForm
from survey.models.households import HouseholdMember, Household
from survey.models import WebAccess, SurveyAllocation, SurveyHouseholdListing


@permission_required('auth.can_view_households')
def new(request, household_id):
    member_form = HouseholdMemberForm()
    breadcrumbs = [('Households', reverse('list_household_page')), ]
    try:
        household = Household.objects.get(id=household_id)
        breadcrumbs.append(('Household', reverse(
            'view_household_page', args=(household_id, ))),)
        if request.method == 'POST':
            member_form = HouseholdMemberForm(data=request.POST)
            interviewer = household.last_registrar
            survey = SurveyAllocation.get_allocation(interviewer)
            if member_form.is_valid():
                household_member = member_form.save(commit=False)
                household_member.household = household
                household_member.registrar = household.last_registrar
                household_member.survey_listing = SurveyHouseholdListing.get_or_create_survey_listing(interviewer,
                                                                                                      survey)
                household_member.registration_channel = WebAccess.choice_name()
                household_member.save()
                messages.success(
                    request, 'Household member successfully created.')
                return HttpResponseRedirect('/households/%s/' % (str(household_id)))
    except Household.DoesNotExist:
        messages.error(
            request, 'There are  no households currently registered  for this ID.')
        return HttpResponseRedirect('/households/')
    request.breadcrumbs(breadcrumbs)
    return render(request, 'household_member/new.html', {'member_form': member_form, 'button_label': 'Create'})


@permission_required('auth.can_view_households')
def edit(request, household_id, member_id):
    household_member = HouseholdMember.objects.get(
        id=member_id, household__id=household_id)
    member_form = HouseholdMemberForm(instance=household_member)

    if request.method == 'POST':
        member_form = HouseholdMemberForm(
            instance=household_member, data=request.POST)
        if member_form.is_valid():
            member_form.save()
            messages.success(request, 'Household member successfully edited.')
            return HttpResponseRedirect('/households/%s/' % (str(household_id)))
    request.breadcrumbs([
        ('Households', reverse('list_household_page')),
        ('Household', reverse('view_household_page', args=(household_id, )))
    ])
    return render(request, 'household_member/new.html',
                  {'member_form': member_form, 'button_label': 'Save'})


def delete(request, household_id, member_id):
    member = HouseholdMember.objects.get(
        id=member_id, household__id=household_id)

    member.delete()

    messages.success(request, 'Household member successfully deleted.')
    return HttpResponseRedirect('/households/%s/' % (str(household_id)))
