# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from lettuce import step, world


@step(u'And I click Survey tab')
def and_i_click_survey_tab(step):
    world.page.click_tab("Survey")

@step(u'Then I should see survey dropdown list')
def then_i_should_see_survey_dropdown_list(step):
    reverse_url_links = ["survey_list_page", "new_survey_page", "add_location_hierarchy", "upload_locations"]
    world.page.see_dropdown(reverse_url_links)

@step(u'And I click Questions tab')
def and_i_click_questions_tab(step):
    world.page.click_tab("Question Bank")

@step(u'Then I should see Questions dropdown list')
def then_i_should_see_questions_dropdown_list(step):
    reverse_url_links = ["list_all_questions","new_question_page"]
    world.page.see_dropdown(reverse_url_links)
