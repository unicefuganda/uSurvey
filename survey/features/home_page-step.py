from lettuce import *

from survey.features.page_objects.accounts import LogoutPage
from survey.features.page_objects.root import AboutPage


@step(u'Given I am not logged in')
def given_i_am_not_logged_in(step):
    world.page = LogoutPage(world.browser)
    world.page.visit()

@step(u'Then I should see the completion map')
def then_i_should_see_under_construction(step):
    world.page.is_text_present("Completion rates:")