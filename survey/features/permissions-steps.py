from lettuce import *
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from survey.features.page_objects.accounts import LogoutPage, LoginPage


@step(u'Given I  am an anonymous user')
def given_i_am_an_anonymous_user(step):
    world.page = LogoutPage(world.browser)
    world.page.visit()

@step(u'Then I should see anonymous user allowed tabs')
def then_i_should_see_anonymous_user_allowed_tabs(step):
    world.page = LoginPage(world.browser)
    world.page.check_anonymous_user_allowed_tabs()

@step(u'And I should not be seeing above anonymous user level tabs')
def and_i_should_not_be_seeing_above_anonymous_user_level_tabs(step):
    world.page.check_anonymous_user_not_allowed_tabs()

def set_permissions(group, permissions_codename_list):
    auth_content = ContentType.objects.get_for_model(Permission)
    for codename in permissions_codename_list:
        permission, out = Permission.objects.get_or_create(codename=codename, content_type=auth_content)
        group.permissions.add(permission)

@step(u'Given I have a data entry user')
def given_i_have_a_data_entry_user(step):
    data_entry = Group.objects.create(name='data_entry')
    world.user = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
    data_entry.user_set.add(world.user)
    set_permissions(data_entry, ['can_view_households', 'can_view_investigators'])

@step(u'And I login that user')
def and_i_login_that_user(step):
    world.page = LoginPage(world.browser)
    world.page.visit()
    world.page.login(world.user)

@step(u'Then I should see data entry allowed tabs')
def then_i_should_see_data_entry_allowed_tabs(step):
    world.page.check_data_entry_allowed_tabs()

@step(u'And I should not be seeing above data entry level tabs')
def and_i_should_not_be_seeing_above_data_entry_level_tabs(step):
    world.page.check_data_entry_not_allowed_tabs()

@step(u'Given I have a researcher user')
def given_i_have_a_researcher_user(step):
    researcher = Group.objects.create(name='researcher')
    world.user = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
    researcher.user_set.add(world.user)
    set_permissions(researcher, ['can_view_aggregates', 'can_view_households', 'can_view_batches', 'can_view_investigators'])

@step(u'And I should not be seeing above researcher level tabs')
def and_i_should_not_be_seeing_above_researcher_level_tabs(step):
    world.page.check_researcher_not_allowed_tabs()

@step(u'Then I should see researcher allowed tabs')
def then_i_should_see_researcher_allowed_tabs(step):
    world.page.check_researcher_allowed_tabs()

@step(u'Given I have a admin user')
def given_i_have_a_admin_user(step):
    admin = Group.objects.create(name='mics_admin')
    world.user = User.objects.create_user('rajni', 'Rajni@kant.com', 'I_Rock')
    admin.user_set.add(world.user)
    set_permissions(admin, ['can_view_aggregates', 'can_view_households', 'can_view_batches', 'can_view_investigators', 'can_view_users'])

@step(u'Then I should all tabs')
def then_i_should_all_tabs(step):
    world.page.check_all_tabs()

@step(u'Then I should not see notify investigators drop-down')
def then_i_should_not_see_notify_investigators_drop_down(step):
    world.page.check_notify_investigators_drop_down_is_not_present()
