from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import LocationTypeDetails, LocationCode, UploadErrorLog
from survey.services.csv_uploader import UploadService


class UploadLocation(UploadService):
    MODEL = 'LOCATIONS'

    def _get_location_type(self, headers):
        location_types = []
        row_regrouping =[]
        for header in headers:
            type_ = LocationType.objects.filter(name=header, slug=slugify(header))[0]
            detail = type_.details.all()[0]
            location_types.append({'type': type_, 'detail':detail})
            row_regrouping.append(2 if detail.has_code else 1)
        return location_types, row_regrouping

    def _create_locations(self, csv_rows, location_types, row_regrouping):
        first_level_location = LocationTypeDetails.objects.all()[0].country
        for index, row in enumerate(csv_rows):
            tree_parent = first_level_location
            for x_index, cell_value in enumerate(self.regroup_with_code(row, row_regrouping)):
                tree_parent = self._create_location_and_code(cell_value, index, tree_parent, location_types[x_index])

    def regroup_with_code(self, row, group_size): # see test...
        new_row = []
        pos = 0
        for size in group_size:
            new_row.append(row[pos:pos+size])
            pos = pos+size
        return new_row

    def _create_location_and_code(self, cell_value, index, tree_parent, location_type):
        type_ = location_type['type']
        location_detail = location_type['detail']
        if not cell_value[-1] and location_detail.required:
            self.log_error(index+2,
                           "Missing data: %sName should not be empty."%type_.name)
        else:
            tree_parent = Location.objects.get_or_create(name=cell_value[-1].strip(), type=type_, tree_parent=tree_parent)[0]
            if location_detail.has_code:
                self._create_code(index, tree_parent, location_type, code=cell_value[0])
        return tree_parent

    def _create_code(self, index, tree_parent, location_type, code):
        type_ = location_type['type']
        location_detail = location_type['detail']
        if len(code) != location_detail.length_of_code:
            self.log_error(index+2,
                               "%sCode is shorter or longer than the required %d digits."%(type_.name,  location_detail.length_of_code))
        else:
            LocationCode.objects.create(location=tree_parent, code=code)

    def upload(self):
        headers, rows = self.csv_uploader.split_content()
        cleaned_headers = self.remove_trailing('Name', in_array=headers, exclude='Code')
        if not cleaned_headers:
            UploadErrorLog.objects.create(model=self.MODEL, filename=self.file.name,
                                          error='Locations not uploaded. %s is not a valid csv file.' % self.file.name)
        else:
            location_types, row_regrouping = self._get_location_type(cleaned_headers)
            self._create_locations(rows, location_types, row_regrouping)
