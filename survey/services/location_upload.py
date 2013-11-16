from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import LocationTypeDetails, LocationCode
from survey.services.csv_uploader import UploadService


class UploadLocation(UploadService):
    MODEL = 'LOCATIONS'

    def __init__(self, file):
        super(UploadLocation, self).__init__(file)
        self.REQUIRED_TYPES = {}

    def _get_location_type(self, headers, regroup_headers_row):
        location_types = []
        for index, header in enumerate(headers):
            header = header.strip()
            if not header.endswith('Code'):
                header = header.replace('Name', '')
                location_type = LocationType.objects.filter(name=header, slug=slugify(header))

                if not location_type.exists():
                    return False, 'Location type - %s not found.' % header
                type = location_type[0]
                detail = type.details.all()
                if not detail:
                    return False, 'Location type details for %s not found.'%header

                self.REQUIRED_TYPES[type.name] = detail[0].required
                location_types.append(type)
                if detail[0].has_code:
                    if index==0 or headers[index-1].replace('Code','') != type.name:
                        return False, '%sCode column should be before %sName column. Please refer to input file format.'%(type.name, type.name)
                    regroup_headers_row.append(2)
                else:
                    if headers[index-1].replace('Code','') == type.name:
                        return False, '%s has no code. The column %sCode should be removed. Please refer to input file format.'%(type.name, type.name)
                    regroup_headers_row.append(1)

        headers = self.remove_trailing('Name', in_array=headers, exclude='Code')
        ordered_types = [type.name for type in LocationTypeDetails.get_ordered_types().exclude(name__iexact='country')]
        if not ordered_types == headers:
            return False, 'Location types not in order. Please refer to input file format.'
        return location_types, ''

    def _create_locations(self, reader, headers, location_types, regroup_headers_row):
        for index, row in enumerate(reader):
            tree_parent = LocationTypeDetails.objects.all()[0].country
            for x_index, cell_value in enumerate(self.regroup_with_code(row, regroup_headers_row)):
                try:
                    if not cell_value[-1]:
                        if self.REQUIRED_TYPES[headers[x_index]]:
                            return False, "Locations not uploaded. Missing data: %sName on row %d should not be empty."%(headers[x_index], index+1)
                    else:
                        type = location_types[x_index]
                        tree_parent = Location.objects.get_or_create(name=cell_value[-1].strip(), type=type, tree_parent=tree_parent)[0]
                        if len(cell_value) ==2:
                            code = cell_value[0]
                            detail = type.details.all()[0]
                            if len(code)!= detail.length_of_code:
                                return False, "Locations not uploaded. %sCode on row %d is shorter than the required %d digits."%(type.name, index+1, detail.length_of_code)
                            LocationCode.objects.create(location=tree_parent, code=code)
                except IndexError:
                    continue
        return True, "Locations successfully uploaded."

    def regroup_with_code(self, row, group_size):
        new_row = []
        pos = 0
        for size in group_size:
            new_row.append(row[pos:pos+size])
            pos = pos+size
        return new_row

    def upload(self):
        regroup_headers_row = []
        headers, reader = self.csv_uploader.split_content()
        cleaned_headers = self.remove_trailing('Name', in_array=headers, exclude='Code')
        if not cleaned_headers:
            return False, 'Locations not uploaded. %s is not a csv file.'%self.file.name
        location_types, message = self._get_location_type(headers, regroup_headers_row)
        if not location_types:
            return False, 'Locations not uploaded. ' + message
        return self._create_locations(reader, cleaned_headers, location_types, regroup_headers_row)