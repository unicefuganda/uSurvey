from lettuce import *
from random import randint
from page_objects import *
from django.contrib.auth.models import User, Group
from survey.features.page_objects.accounts import LoginPage, LogoutPage
from survey.features.page_objects.users import NewUserPage, UsersListPage, UsersDetailsPage
from survey.models_file import *


@step(u'Given I am logged in as a superuser')
def given_i_am_logged_in_as_a_superuser(step):
    world.user = User.objects.create(username='Rajni', email='rajni@kant.com', password='I_Rock', first_name='some name', last_name='last_name')
    world.user.is_superuser = True
    world.user.save()
    UserProfile.objects.create(user=world.user, mobile_number='123456666')
    world.page = LoginPage(world.browser)
    world.page.visit()
    world.page.login(world.user)


@step(u'And I visit new user page')
def and_i_visit_new_user_page(step):
    world.page = NewUserPage(world.browser)
    world.page.visit()


@step(u'Then I see all  new user fields')
def then_i_see_all_new_user_fields(step):
    world.page.valid_page()


@step(u'And I click submit')
def and_i_click_submit(step):
    world.page.submit()


@step(u'And I have a group')
def and_i_have_a_group(step):
    world.group = Group.objects.create(name="kojo")


@step(u'Then I fill all necessary new user fields')
def then_i_fill_all_necessary_new_user_fields(step):
    world.user_data = {
        'username': 'babyrajni',
        'password1': 'baby_kant',
        'password2': 'baby_kant',
        'first_name': 'Baby',
        'last_name': 'Kant',
        'mobile_number': '123456789',
        'email': 'baby@ka.nt',
        'groups': world.group.id,
    }

    world.page.fill_valid_values(world.user_data)


@step(u'Then I should see user successfully registered')
def then_i_should_see_user_successfully_registered(step):
    world.page.see_user_successfully_registered()


def logout(world):
    world.page = LogoutPage(world.browser)
    world.page.visit()


def login(user, world):
    world.page = LoginPage(world.browser)
    world.page.visit()
    world.page.login(user)


@step(u'And I can login that user successfully')
def and_i_can_login_that_user_successfully(step):
    logout(world)
    user = User.objects.get(username=world.user_data['username'])
    login(user, world)
    world.page.see_home_page_and_logout_link(user.get_full_name())


@step(u'Then I fill an existing mobile number')
def then_i_fill_an_existing_mobile_number(step):
    world.user_data = {
        'mobile_number': '123456789',
    }

    user = User.objects.create(username='some_other_name')
    UserProfile.objects.create(user=user, mobile_number=world.user_data['mobile_number'])

    world.page.fill_valid_values(world.user_data)
    world.page.submit()


@step(u'Then I should see existing mobile number error message')
def then_i_should_see_existing_mobile_number_error_message(step):
    world.page.is_text_present('%s is already associated with a different user.' % world.user_data['mobile_number'])


@step(u'Then I fill an existing username')
def then_i_fill_an_existing_username(step):
    world.user_data = {
        'username': 'babyrajni',
    }
    User.objects.create(username=world.user_data['username'])

    world.page.fill_valid_values(world.user_data)
    world.page.submit()


@step(u'Then I should see existing username error message')
def then_i_should_see_existing_username_error_message(step):
    world.page.is_text_present('%s is no longer available.' % world.user_data['username'])


@step(u'Then I fill an existing email')
def then_i_fill_an_existing_email(step):
    world.user_data = {
        'email': 'haha@ha.ha',
    }
    User.objects.create(email=world.user_data['email'])

    world.page.fill_valid_values(world.user_data)
    world.page.submit()


@step(u'Then I should see existing email error message')
def then_i_should_see_existing_email_error_message(step):
    world.page.is_text_present('%s is already associated with a different user.' % world.user_data['email'])


@step(u'Then I fill a not allowed username')
def then_i_fill_a_not_allowed_username(step):
    not_allowed_username = 'haha#%&&**!'
    world.user_data = {
        'username': not_allowed_username,
    }
    User.objects.create(username=world.user_data['username'])

    world.page.fill_valid_values(world.user_data)
    world.page.submit()


@step(u'Then I should see not allowed username error message')
def then_i_should_see_not_allowed_username_error_message(step):
    world.page.is_text_present("username may contain only letters characters.")


@step(u'And I have 100 users')
def and_i_have_users(step):
    for i in range(100):
        random_suffix_number = str(randint(1, 99999))
        try:
            user = User.objects.create_user('user' + random_suffix_number, random_suffix_number + "@gmail.com",
                                            'pass' + random_suffix_number)
            UserProfile.objects.create(mobile_number=random_suffix_number, user=user)
        except:
            pass


@step(u'And I visit the users list page')
def and_i_visit_the_users_list_page(step):
    world.page = UsersListPage(world.browser)
    world.page.visit()


@step(u'Then I should see a list of users')
def then_i_should_see_a_list_of_users(step):
    world.page.validate_users_listed()
    world.page.validate_displayed_headers()
    world.page.validate_users_paginated()

@step(u'Then I should see the users information in a form')
def then_i_should_see_the_users_information_in_a_form(step):
    world.page = UsersDetailsPage(world.browser)
    world.page.set_user(world.user)
    world.page.assert_form_has_infomation()


@step(u'When I modify the users information')
def when_i_modify_the_users_information(step):
    world.page.modify_users_information()


@step(u'And I click the update button')
def and_i_click_the_update_button(step):
    world.page.click_update_button()


@step(u'Then I should see user information updated successfully')
def then_i_should_see_user_information_saved_successfully(step):
    world.page.assert_user_saved_sucessfully()

@step(u'And I see that username is readonly')
def and_i_see_that_username_is_readonly(step):
    world.page.assert_username_is_readonly()

@step(u'Then I should not see the groups field')
def then_i_should_not_see_the_groups_field(step):
    world.page.is_group_input_field_visible(False)

@step(u'Then I should see the groups field')
def then_i_should_see_the_groups_field(step):
    world.page.is_group_input_field_visible(True)

@step(u'And I select edit action')
def and_i_select_edit_action(step):
    world.page.click_link_by_text(" Edit Profile")
    world.page = UsersDetailsPage(world.browser)