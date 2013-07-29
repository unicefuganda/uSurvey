from lettuce import *
from page_objects import *
from django.contrib.auth.models import User


@step(u'Given I am logged in as a superuser')
def given_i_am_logged_in_as_a_superuser(step):
    world.user = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')

@step(u'And I visit new user page')
def and_i_visit_new_user_page(step):
    world.page = NewUserPage(world.browser)
    world.page.visit()

@step(u'Then I see all  new user fields')
def then_i_see_all_new_user_fields(step):
    world.page.valid_page()

@step(u'And I click submit')
def and_i_click_submit(step):
    assert False, 'This step must be implemented'
@step(u'Then I should see errors about required fields')
def then_i_should_see_errors_about_required_fields(step):
    assert False, 'This step must be implemented'