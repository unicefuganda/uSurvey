from rapidsms.contrib.locations.models import Location, LocationType

from survey.models import UploadErrorLog, EnumerationArea
from survey.services.csv_uploader import UploadService


class UploadEA(UploadService):
    MODEL = 'EA'

    @classmethod
    def parents_locations_match(cls, location, given_parents):
        location_parents = location.get_ancestors().values_list('name', flat=True)
        check = [parent_name in location_parents for parent_name in given_parents]
        return check.count(True) == len(given_parents)

    def check_errors_(self, index,  row, headers, skip_column, lowest_location_column):
        lowest_location_name = row[lowest_location_column]
        location = Location.objects.filter(name=lowest_location_name, tree_parent__name__iexact=row[skip_column-1].lower())
        if not location.exists():
            self.log_error(index+1, 'There is no %s with name: %s, in %s.' %
                                    (headers[lowest_location_column].lower(), row[lowest_location_column], row[skip_column-1]))
            return
        if not self.parents_locations_match(location[0], row[:skip_column-1]):
            self.log_error(index+1, 'The location hierarchy %s >> %s does not exist.' % ((' >> '.join(row[:skip_column])), lowest_location_name))
            return
        return location[0]

    def check_location_errors(self, index, row, headers):
        first_ea_column_number = headers.index('EA')
        return self.check_errors_(index,  row, headers,
                                  skip_column=first_ea_column_number, lowest_location_column=-2)

    def save_ea(self, index, row, location, survey):
        first_ea_column_number = -3
        second_ea_column_number = -1
        ea_name = row[first_ea_column_number] or row[second_ea_column_number]
        if ea_name:
            ea = EnumerationArea.objects.get_or_create(name=ea_name, survey=survey)[0]
            ea.locations.add(location)
        else:
            self.log_error(index+1, 'Enumeration Area name required.')

    def create_ea(self, reader, headers, survey):
        for index, row in enumerate(reader):
            location = self.check_location_errors(index, row, headers)
            if location:
                self.save_ea(index, row, location, survey)

    def upload(self, survey):
        headers, reader = self.csv_uploader.split_content()
        cleaned_headers = self.remove_trailing('Name', in_array=headers)
        if not cleaned_headers:
            UploadErrorLog.objects.create(model=self.MODEL, filename=self.file.name,
                                          error='Enumeration Areas not uploaded. %s is not a valid csv file.' % self.file.name)
        else:
            self.create_ea(reader, cleaned_headers, survey)

class UploadEACSVLayoutHelper(object):

    def __init__(self):
        self.headers = self._header_format()

    @classmethod
    def _header_format(cls):
        types = list(LocationType.objects.exclude(name__iexact="country").values_list('name', flat=True))
        types.insert(-1, 'EA')
        types.append('EA')
        return types

    def table_layout_example(self):
        headers = map(lambda header: header.lower(), self.headers)
        if headers != ['ea', 'ea']:
            row1 = [header+'_0' for header in headers]
            row1[-1] = ''
            row2 = list(row1)
            row2[-2] += '_b'
            row3 = [header+'_1' for header in headers]
            row3[-3] = ''
            row4 = list(row3)
            row4[-1] += '_b'
            return [row1, row2, row3, row4]
        return [["No Location/LocationType added yet. Please add those first."]]

