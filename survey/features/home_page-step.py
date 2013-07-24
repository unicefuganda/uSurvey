from page_objects import *
from random import randint
from survey.models import *
from rapidsms.contrib.locations.models import *
from django.template.defaultfilters import slugify
from lettuce import *
from django.contrib.auth.models import User

@step(u'Given I am not logged in')
def given_i_am_not_logged_in(step):
    world.page = LogoutPage(world.browser)
    world.page.visit()

@step(u'Then I should see under construction')
def then_i_should_see_under_construction(step):
    world.page.see_under_construction()

@step(u'Then I should see the about link')
def then_i_should_see_the_about_link(step):
    world.page.see_the_about_link()

@step(u'And If I click the about link')
def and_if_i_click_the_about_link(step):
    world.page.click_the_about_link()

@step(u'Then I am in the about page')
def then_i_am_in_the_about_page(step):
    world.page.check_browser_is_in_about_page()

@step(u'And I should see the about text provided by panwar')
def and_i_should_see_the_about_text_provided_by_panwar(step):
    world.page = AboutPage(world.browser)
    world.page.see_the_about_text_provided_by_panwar()