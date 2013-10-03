from random import randint

from lettuce import *
from survey.models.householdgroups import HouseholdMemberGroup, GroupCondition

from survey.features.page_objects.household_member_groups import GroupConditionListPage, GroupsListingPage, AddConditionPage, AddGroupPage, GroupConditionModalPage, GroupDetailsPage, AddNewConditionToGroupPage, DeleteHouseholdMemberGroup

@step(u'And I have 10 conditions')
def and_i_have_10_conditions(step):
    for i in xrange(10):
        try:
            GroupCondition.objects.create(value=i, attribute='AGE', condition="EQUALS")
        except Exception:
            pass


@step(u'And I visit conditions listing page')
def and_i_visit_conditions_listing_page(step):
    world.page = GroupConditionListPage(world.browser)
    world.page.visit()


@step(u'And I should see the conditions list')
def and_i_should_see_the_conditions_list(step):
    world.page.validate_fields()


@step(u'And I have a condition')
def and_i_have_a_condition(step):
    world.condition = GroupCondition.objects.create(value=5, attribute='AGE', condition="EQUALS")


@step(u'And I have 100 groups with that condition')
def and_i_have_100_groups_with_that_condition(step):
    for i in xrange(100):
        try:
            HouseholdMemberGroup.objects.create(order=i, name="group %d" % i)
        except Exception:
            pass


@step(u'And I visit groups listing page')
def and_i_visit_groups_listing_page(step):
    world.page = GroupsListingPage(world.browser)
    world.page.visit()


@step(u'Then I should see the groups list paginated')
def then_i_should_see_the_groups_list_paginated(step):
    world.page.validate_fields()
    world.page.validate_pagination()


@step(u'When I click the add button')
def when_i_click_the_add_button(step):
    world.page.click_link_by_text(" Add Condition")


@step(u'Then I should see the new condition form')
def then_i_should_see_the_new_condition_form(step):
    world.page.is_text_present("New condition")


@step(u'And I visit the new condition page')
def and_i_visit_the_new_condition_page(step):
    world.page = AddConditionPage(world.browser)
    world.page.visit()


@step(u'When I fill in the condition details')
def when_i_fill_in_the_condition_details(step):
    data = {'attribute': 'AGE',
            'value': '9'}
    world.page.fill_valid_values(data)
    world.page.fill('value', '9')


@step(u'And I click save button')
def and_i_click_save_button(step):
    world.page.submit()


@step(u'Then I should see that the condition was saved on the condition list page')
def then_i_should_see_that_the_condition_was_saved_successfully(step):
    world.page = GroupConditionListPage(world.browser)
    world.page.validate_url()
    world.page.see_success_message('Condition', 'added')


@step(u'And I visit the new group page')
def and_i_visit_the_new_group_page(step):
    world.page = AddGroupPage(world.browser)
    world.page.visit()


@step(u'When I fill in the group details')
def when_i_fill_in_the_group_details(step):
    data = {'name': 'aged between 15 and 49',
            'order': 1,
    }
    world.page.fill_valid_values(data)


@step(u'Then I should see that the group was saved successfully')
def then_i_should_see_that_the_group_was_saved_successfully(step):
    world.page.see_success_message('Group', 'added')


@step(u'When I click the add new condition')
def when_i_click_the_add_new_condition(step):
    world.page.click_link_by_text("Add Eligibility Criteria ")


@step(u'Then I should see the modal open')
def then_i_should_see_the_modal_open(step):
    world.page = GroupConditionModalPage(world.browser)
    world.page.validate_contents()


@step(u'And I click the new condition form save button')
def and_i_click_the_save_button(step):
    world.page.click_button("save_condition_button")


@step(u'Then I should see the condition saved on create group page')
def then_i_should_see_the_condition_was_saved_successfully(step):
    world.page = AddGroupPage(world.browser)
    world.page.validate_url()
    world.page.see_success_message("Condition", "added")


@step(u'And I should see the new condition in the groups form')
def and_i_should_see_the_new_condition_in_the_groups_form(step):
    latest_condition = GroupCondition.objects.get(value='9', attribute="AGE", condition="EQUALS")
    world.page.validate_latest_condition(latest_condition)


@step(u'And I have 2 conditions')
def and_i_have_2_conditions(step):
    world.condition_1 = GroupCondition.objects.create(value=False, attribute="GENDER", condition="EQUALS")
    world.condition_2 = GroupCondition.objects.create(value=40, attribute="AGE", condition="EQUALS")


@step(u'When I fill name and order')
def when_i_fll_name_and_order(step):
    data = {'name': 'aged between 15 and 49',
            'order': 1}
    world.page.fill_valid_values(data)


@step(u'And I select conditions')
def and_i_select_conditions(step):
    world.page.select('conditions', [world.condition_1.pk, world.condition_2.pk])


@step(u'Then I should see the form errors of required fields')
def then_i_should_see_the_form_errors_of_required_fields(step):
    world.page.is_text_present("This field is required.")

@step(u'And I have member group with conditions')
def and_i_have_member_group_with_conditions(step):
    world.condition_1 = GroupCondition.objects.create(value='True', attribute="GENDER", condition="EQUALS")
    world.condition_2 = GroupCondition.objects.create(value=35, attribute="AGE", condition="EQUALS")
    world.group = HouseholdMemberGroup.objects.create(order=1, name="group 1")
    world.condition_1.groups.add(world.group)
    world.condition_2.groups.add(world.group)


@step(u'And I click view conditions link')
def and_i_click_view_conditions_link(step):
    world.page.click_link_by_text(" Criteria")


@step(u'Then I should see a list of conditions')
def then_i_should_see_a_list_of_conditions(step):
    world.page = GroupDetailsPage(world.browser, world.group)
    world.page.validate_fields()


@step(u'When I click Groups tab')
def when_i_click_groups_tab(step):
    world.page.click_link_by_text("Groups")


@step(u'Then I should see group dropdown list')
def then_i_should_see_group_dropdown_list(step):
    reverse_url_links = ["household_member_groups_page", "new_household_member_groups_page", "show_group_condition",
                         "new_group_condition"]
    world.page.see_dropdown(reverse_url_links)


@step(u'And I select a condition')
def and_i_select_a_condition(step):
    world.page.select("conditions", [world.condition.pk])


@step(u'When I click the add group button')
def when_i_click_the_add_group_button(step):
    world.page.click_link_by_text(" Add Group")


@step(u'Then I should go to add group page')
def then_i_should_go_to_add_group_page(step):
    world.page = AddGroupPage(world.browser)
    world.page.validate_url()


@step(u'When I select gender as attribute')
def when_i_select_gender_as_attribute(step):
    world.page.select('attribute', ['GENDER'])


@step(u'Then I should see only Equals as available for condition')
def then_i_should_see_only_equals_as_available_for_condition(step):
    world.page.see_select_option(['EQUALS'], 'condition')


@step(u'And male and female for values')
def and_male_and_female_for_values(step):
    world.page.see_select_option(['Male', 'Female'], 'value')


@step(u'When I select general as attribute')
def when_i_select_general_as_attribute(step):
    world.page.select('attribute', ['GENERAL'])


@step(u'And HEAD for values')
def and_head_for_values(step):
    world.page.find_by_css('input[name=value][readonly=readonly]', 'HEAD')


@step(u'When I select age as attribute')
def when_i_select_age_as_attribute(step):
    world.page.select('attribute', ['AGE'])


@step(u'And If I add in a negative number')
def and_if_i_add_in_a_negative_number(step):
    world.page.fill('value', '-8')


@step(u'Then I see error age cannot be negative')
def then_i_should_see_error(step):
    world.page.is_text_present('Age cannot be negative.')


@step(u'When I click on add condition button')
def when_i_click_on_add_condition_button(step):
    world.page.click_link_by_text(" Add Condition")


@step(u'Then I should see a new condition form for this group')
def then_i_should_see_a_new_condition_form(step):
    world.page = AddNewConditionToGroupPage(world.browser, world.group)
    world.page.validate_url()
    world.page.validate_fields_present(['Attribute', 'Condition', 'Value'])


@step(u'And When I fill condition details')
def and_when_i_fill_condition_details(step):
    world.data = {
        'attribute': 'AGE',
        'condition': 'EQUALS'
        }
    world.page.fill_valid_values(world.data)
    world.page.fill('value', '9')

@step(u'And I should see the newly added condition on that page')
def and_i_should_see_the_newly_added_condition_on_that_page(step):
    world.page.see_success_message("Condition", "added")
    world.page.validate_fields_present([world.data['attribute'], world.data['condition'], '9'])

@step(u'And I click edit group link')
def and_i_click_edit_group_link(step):
    world.page.click_link_by_text(" Edit")

@step(u'When I fill in edited group details')
def when_i_fill_in_edited_group_details(step):
    data = {'name': 'aged between 15 and 39',
            'order': 1,
    }
    world.page.fill_valid_values(data)

@step(u'Then I should see that the group was edited successfully')
def then_i_should_see_that_the_group_was_edited_successfully(step):
    world.page.see_success_message("Group", "edited")

@step(u'Then I should see the groups details in an edit group form')
def then_i_should_see_the_groups_details_in_an_edit_group_form(step):
    form = {'name': 'Name',
            'order': 'Order'}
    form_values = {'name': world.group.name,
                   'order': world.group.order }
    world.page.validate_form_present(form)
    world.page.validate_form_values(form_values)

@step(u'And I select new conditions')
def and_i_select_new_conditions(step):
    new_condition = GroupCondition.objects.create(value=39, attribute='AGE', condition="LESS_THAN")
    world.page.select_multiple('#id_conditions', world.condition_1, new_condition)

@step(u'And I click delete group link')
def and_i_click_delete_group_link(step):
    world.page.click_link_by_text(" Delete")
    world.page = DeleteHouseholdMemberGroup(world.browser, world.group)

@step(u'Then I should see a delete confirmation modal')
def then_i_should_see_a_delete_confirmation_modal(step):
    world.page.see_confirm_delete_message(world.group.name)

@step(u'When I click yes')
def when_i_click_yes(step):
    world.page.click_link_by_text("Yes")

@step(u'Then I should see that the group was deleted successfully')
def then_i_should_see_that_the_group_was_deleted_successfully(step):
    world.page.see_success_message("Group", "deleted")

@step(u'And I click delete condition link')
def and_i_click_delete_condition_link(step):
    world.page.click_link_by_text(" Delete")

@step(u'Then I should see a delete condition confirmation modal')
def then_i_should_see_a_delete_condition_confirmation_modal(step):
  world.page.see_confirm_delete_message(world.condition_1.__str__())
  world.page.is_text_present("It is attached to the following groups:")
  world.page.find_link_by_text(world.group.name)

@step(u'Then I should see that the condition was deleted successfully')
def then_i_should_see_that_the_condition_was_deleted_successfully(step):
    world.page.see_success_message("Condition", "deleted")