from lettuce import *
from page_objects import *
from django.contrib.auth.models import User, Group
from survey.models import *

@step(u'Then I see user settings link')
def then_i_see_user_settings_link(step):
    world.page.see_user_settings_link(world.user)

@step(u'And I click user settings link')
def and_i_click_user_settings_link(step):
    world.page.click_user_settings(world.user)

@step(u'Then I see edit profile and logout link')
def then_i_see_edit_profile_and_logout_link(step):
    world.page.assert_user_can_see_profile_and_logout_link()