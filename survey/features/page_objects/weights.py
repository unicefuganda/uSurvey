from survey.features.page_objects.base import PageObject

__author__ = 'mnandri'


class ListLocationWeightsPage(PageObject):
    url = "/locations/weights/"


class ListLocationWeightsErrorLogPage(PageObject):
    url = "/locations/weights/error_logs/"