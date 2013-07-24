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

@step(u'Then I should see the about text provided by panwar')
def then_i_should_see_the_about_text_provided_by_panwar(step):
    world.page.see_the_about_text_provided_by_panwar()