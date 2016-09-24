from survey.features.page_objects.base import PageObject


class NewIndicatorPage(PageObject):
    url = '/indicators/new/'


class ListIndicatorPage(PageObject):
    url = '/indicators/'

    def see_indicators(self, indicators):
        list_titles = ['Indicator', 'Description',
                       'Module', 'Measure', 'Actions']
        values = [[field.name, field.description, field.module.name,
                   field.measure] for field in indicators]
        values.append(list_titles)
        fields = [field for fields in values for field in fields]
        self.validate_fields_present(fields)


class SimpleIndicatorGraphPage(PageObject):

    def __init__(self, browser, indicator):
        self.indicator = indicator
        self.browser = browser
        self.url = "/indicators/%s/simple/" % self.indicator.id
