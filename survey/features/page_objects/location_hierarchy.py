from survey.features.page_objects.base import PageObject


class AddLocationHierarchyPage(PageObject):
    def __init__(self, browser):
        super(AddLocationHierarchyPage, self).__init__(browser)
        self.url = '/add_location_hierarchy/'