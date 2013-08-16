from page_objects import *
from random import randint
from survey.models import *
from rapidsms.contrib.locations.models import *
from django.template.defaultfilters import slugify
from lettuce import *
from django.contrib.auth.models import User

@step(u'Given I have a user')
def given_i_have_a_user(step):
    world.user = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock', first_name='Rajin', last_name="Kant")
    profile = UserProfile.objects.create(user=world.user, mobile_number='2222222223')

@step(u'And I visit the login page')
def and_i_visit_the_login_page(step):
    world.page = LoginPage(world.browser)
    world.page.visit()

@step(u'And I login a user')
def and_i_login_a_user(step):
    world.page = LoginPage(world.browser)
    world.page.login(world.user)

@step(u'Then I should see home page and logout link')
def then_i_should_see_home_page_and_logout_link(step):
    world.page.see_home_page_and_logout_link(world.user.get_full_name())

@step(u'And I am in the home page')
def and_i_am_in_the_home_page(step):
    world.page = HomePage(world.browser)
    world.page.visit()

@step(u'And I click the login link')
def and_i_click_the_login_link(step):
    world.page.click_the_login_link()

@step(u'Then I should see new investigator with logout link')
def then_i_should_see_new_investigator_with_logout_link(step):
    world.page = NewInvestigatorPage(world.browser)
    world.page.see_username_link(world.user.get_full_name())

@step(u'Then I should see list investigator with logout link')
def then_i_should_see_list_investigator_with_logout_link(step):
    world.page = InvestigatorsListPage(world.browser)
    world.page.see_username_link(world.user.get_full_name())

@step(u'Then I should see new household page with logout link')
def then_i_should_see_new_household_page_with_logout_link(step):
    world.page = NewHouseholdPage(world.browser)
    world.page.see_username_link(world.user.get_full_name())

@step(u'Then I should see aggregate status page with logout link')
def then_i_should_see_aggregate_status_page_with_logout_link(step):
    world.page = AggregateStatusPage(world.browser)
    world.page.see_username_link(world.user.get_full_name())

@step(u'Then I should see download excel page with logout link')
def then_i_should_see_download_excel_page_with_logout_link(step):
    world.page = DownloadExcelPage(world.browser)
    world.page.see_username_link(world.user.get_full_name())

@step(u'Then I should see new user page with logout link')
def then_i_should_see_new_user_page_with_logout_link(step):
    world.page = NewUserPage(world.browser)
    world.page.see_username_link(world.user.get_full_name())
