# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from time import sleep
from survey.features.page_objects.base import PageObject
from nose.tools import assert_equals

class FormulaShowPage(PageObject):
    def __init__(self, browser, formula):
        self.browser = browser
        self.formula = formula
        self.url = "/batches/%s/formulae/%s/" % (self.formula.indicator.batch.pk, self.formula.pk)

    def choose_location(self, location):
        self.fill_in_with_js('$("#location-%s")' % location.type.slug, location.id)

    def presence_of_computed_value(self, computed_value):
        self.is_text_present(str(computed_value))

    def presence_of_bar_graph_for_villages(self, data):
        for village, value in data.items():
            self.is_text_present(village.name)
            self.is_text_present(str(int(value)))

    def presence_of_bar_graph_for_households(self,data):
        for key, value in data.items():
            for household, val in value.items():
                self.is_text_present(household.text)
                self.is_text_present(str(val))

    def presence_of_bar_chart_for_all_the_options(self,data):
        for option, value in data.items():
            self.is_text_present(str(option))
            self.is_text_present(str(int(value)))

    def presence_of_stacked_bar_graph_for_villages(self,data):
        for village, value in data.items():
            self.is_text_present(village.name)
            for option, val in value.items():
                self.is_text_present(str(option))

    def presence_of_tabulated_results_for_households(self,data):
        for household, value in data.items():
            self.is_text_present(household.get_head().surname)
            for question, val in value.items():
                self.is_text_present(question.text)
                if type(val) == int:
                    self.is_text_present(str(val))
                else:
                    self.is_text_present(val.text)


class AddBatchPage(PageObject):
    def __init__(self, browser,survey):
        self.browser= browser
        self.survey= survey
        self.url = '/surveys/%s/batches/new/' %survey.pk

    def validate_error_message_on_fields(self):
        self.is_text_present("This field is required.")


class BatchShowPage(PageObject):
    def __init__(self, browser, batch):
        super(BatchShowPage, self).__init__(browser)
        self.url = "/batches/" + str(batch.pk)

    def batch_closed_for_all_locations(self):
        assert len(self.browser.find_by_css('input[checked=checked]')) == 0

    def open_batch_for(self, location):
        self.browser.execute_script('$($("input:checkbox")[0]).parent().bootstrapSwitch("toggleState")')
        sleep(2)

    def close_batch_for(self, location):
        self.browser.execute_script('$($("input:checkbox")[0]).parent().bootstrapSwitch("toggleState")')
        sleep(2)


class EditBatchPage(PageObject):
    def __init__(self, browser, batch,survey):
        self.browser= browser
        self.batch= batch
        self.survey= survey
        self.url = '/surveys/%s/batches/%s/edit/' %(self.survey.id, self.batch.id)


class BatchListPage(PageObject):
    def __init__(self, browser, survey):
        self.browser= browser
        self.survey= survey
        self.url = '/surveys/' + str(self.survey.id) + '/batches/'

    def visit_batch(self, batch):
        self.browser.click_link_by_text(" Open/Close")
        return BatchShowPage(self.browser, batch)

    def click_add_batch_button(self):
        self.browser.click_link_by_text("Add Batch")

    def validate_fields(self):
        self.validate_fields_present([self.survey.name.capitalize(), "Batch Name", "Description", "Actions"])

    def click_link_by_text(self,text):
        self.browser.click_link_by_text(text)

    def validate_page_got_survey_id(self):
        assert self.browser.find_by_css('#survey_id').first.value == str(self.survey.id)

class AssignQuestionToBatchPage(PageObject):
    def __init__(self, browser, batch):
        self.browser= browser
        self.batch= batch
        self.url = '/batches/' + str(self.batch.id) + '/assign_questions/'

    def see_the_question(self, status, question_id):
        assert_equals( status, self.browser.find_by_id("%s-selectable" %question_id).visible)

    def see_the_selected_question(self, status, question_id):
        assert_equals( status, self.browser.find_by_id("%s-selection" %question_id).visible)
