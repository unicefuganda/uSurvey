from lettuce import *
from survey.features.page_objects.root import AboutPage, EditAboutUsPage
from survey.models import AboutUs


@step(u'And I visit the about us page')
def and_i_visit_the_about_us_page(step):
    world.page = AboutPage(world.browser)
    world.page.visit()


@step(u'And I have about us content')
def and_i_have_about_us_content(step):
    world.about_us = AboutUs.objects.create(content="blah blah")


@step(u'Then I should see the sample about us information')
def then_i_should_see_the_sample_about_us_information(step):
    world.page.is_text_present(world.about_us.content)


@step(u'When I click the edit link')
def when_i_click_the_edit_link(step):
    world.page.click_by_css("#edit-about_us")


@step(u'Then I should see the existing content in a text area')
def then_i_should_see_the_existing_content_in_a_text_area(step):
    world.page = EditAboutUsPage(world.browser)
    world.form_data = {'content': world.about_us.content}
    world.page.validate_form_values(world.form_data)


@step(u'When I modify about us content')
def when_i_modify_about_us_content(step):
    world.form_data = {'content': "edited more blah blah blah"}
    world.page.fill_wywget_textarea(world.form_data)


@step(u'Then I should see the content was updated successfully')
def then_i_should_see_the_content_was_updated_successfully(step):
    world.page.see_success_message("About us content", "updated")


@step(u'And I should not see the edit about us button')
def and_i_should_not_see_the_edit_about_us_button(step):
    world.page.assert_edit_link_absent()
