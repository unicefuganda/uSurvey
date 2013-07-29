from lettuce import *
from page_objects import *
from django.contrib.auth.models import User, Group


@step(u'Given I am logged in as a superuser')
def given_i_am_logged_in_as_a_superuser(step):
    user = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
    world.page = LoginPage(world.browser)
    world.page.visit()
    world.page.login(user)

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
    world.group = Group.objects.create()

@step(u'Then I fill all necessary new user fields')
def then_i_fill_all_necessary_new_user_fields(step):
    world.page.fill_valid_values(world.group)

@step(u'Then I should see user successfully registered')
def then_i_should_see_user_successfully_registered(step):
    world.page.see_user_successfully_registered()