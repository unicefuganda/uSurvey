from lettuce import *
from survey.features.page_objects.accounts import ResetPasswordPage

@step(u'And I click user settings link')
def and_i_click_user_settings_link(step):
    world.page.click_user_settings()

@step(u'Then I see edit profile, change password and logout link')
def then_i_see_edit_profile_change_password_and_logout_link(step):
    world.page.assert_user_can_see_profile_and_logout_link()
    
@step(u'Then I click change password link')
def then_i_click_change_password_link(step):
    world.page.click_reset_password_form()
    
@step(u'Then I should see a form asking me to add old password and new password')
def then_i_should_see_a_form_asking_me_to_add_old_password_and_new_password(step):
    world.page = ResetPasswordPage(world.browser)
    world.page.visit()
    world.page.is_change_password_form_visble()
    
@step(u'Then I fill in the old password and new password')
def then_i_fill_in_the_old_password_and_new_password(step):
    world.page.fill('old_password','kant')
    world.page.fill('new_password1','pass')
    world.page.fill('new_password2','pass')
    
@step(u'And I click the change my password button')
def and_i_click_the_change_my_password_button(step):
    world.page.click_change_password_button()
    
@step(u'Then I should see password reset successfully')
def then_i_should_see_password_reset_successfully(step):
    world.page.assert_password_successfully_reset()

@step(u'Then I fill in the wrong old password and correct new password')
def then_i_fill_in_the_wrong_old_password_and_correct_new_password(step):
    world.page.fill('old_password','kantus')
    world.page.fill('new_password1','pass')
    world.page.fill('new_password2','pasq')
    
@step(u'Then I should error that my old password is incorrect')
def then_i_should_error_that_my_old_password_is_incorrect(step):
    world.page.is_incorrect_oldpassword_error_visible()
    world.page.is_password_mismatch()