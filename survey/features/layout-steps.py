# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from lettuce import step, world


@step(u'And I click Survey Administration tab')
def and_i_click_survey_administration_tab(step):
    world.page.click_tab("Survey Administration")


@step(u'Then I should see survey administration dropdown list')
def then_i_should_see_survey_administration_dropdown_list(step):
    reverse_url_links = ["investigators_page", "list_household_page", "list_all_questions", "survey_list_page",
                         "question_module_listing_page", "household_member_groups_page", "bulk_sms", "upload_ea"]
    world.page.see_dropdown(reverse_url_links)


@step(u'And I click Downloads Tab')
def and_i_click_downloads_tab(step):
    world.page.click_tab("Downloads")


@step(u'Then I should see Downloads dropdown list')
def then_i_should_see_downloads_dropdown_list(step):
    reverse_url_links = ['download_excel', 'investigator_report_page']
    world.page.see_dropdown(reverse_url_links)


@step(u'And I click Analysis tab')
def and_i_click_analysis_tab(step):
    world.page.click_tab("Analysis")


@step(u'Then I should see analysis dropdown list')
def then_i_should_see_analysis_dropdown_list(step):
    reverse_url_links = ["simulator_page", "list_indicator_page",
                         "survey_completion_rates", "list_weights_page"]
    world.page.see_dropdown(reverse_url_links)


@step(u'And I click Settings tab')
def and_i_click_settings_tab(step):
    world.page.click_tab("Settings")


@step(u'Then I should see Settings dropdown list')
def then_i_should_see_settings_dropdown_list(step):
    reverse_url_links = ["add_location_hierarchy",
                         "upload_locations", "users_index"]
    world.page.see_dropdown(reverse_url_links)
