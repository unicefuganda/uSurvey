from page_objects import *
from random import randint
from survey.models import *
from rapidsms.contrib.locations.models import *
from django.template.defaultfilters import slugify
from lettuce import *
from django.contrib.auth.models import User

@step(u'Given I have a user')
def given_i_have_a_user(step):
    world.user = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')

@step(u'And I am in the homepage')
def and_i_am_in_the_homepage(step):
    assert False, 'This step must be implemented'

@step(u'And I click the login page')
def and_i_click_the_login_page(step):
    assert False, 'This step must be implemented'

@step(u'And I visit the login page')
def and_i_visit_the_login_page(step):
    world.page = LoginPage(world.browser)
    world.page.visit()

@step(u'And I login a user')
def and_i_login_a_user(step):
    world.page.login(world.user)

@step(u'Then I should see home page and logout link')
def then_i_should_see_home_page_and_logout_link(step):
    world.page.see_home_page_and_logout_link()