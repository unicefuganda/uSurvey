from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import LocationTypeDetails, LocationCode
from survey.services.csv_uploader import CSV_Uploader


class UploadLocation:
    def __init__(self, file):
        self.file = file
        self.REQUIRED_TYPES = {}
        self.csv_uploader = CSV_Uploader(self.file)

    def _get_location_type(self, headers, location_types, regroup_row):
        for index, header in enumerate(headers):
            header = header.strip()
            if header.endswith('Name'):
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
                    regroup_row.append(2)
                else:
                    if headers[index-1].replace('Code','') == type.name:
                        return False, '%s has no code. The column %sCode should be removed. Please refer to input file format.'%(type.name, type.name)
                    regroup_row.append(1)

        headers = self.remove_trailing('Name', in_array=headers)
        ordered_types = [type.name for type in LocationTypeDetails.get_ordered_types().exclude(name__iexact='country')]
        if not ordered_types == headers:
            return False, 'Location types not in order. Please refer to input file format.'
        return True, ''

    def _create_locations(self, reader, headers, location_types, regroup_row):
        for row in reader:
            tree_parent = LocationTypeDetails.objects.all()[0].country
            for x_index, cell_value in enumerate(self.regroup_with_code(row, regroup_row)):
                try:
                    if not cell_value[-1]:
                        if self.REQUIRED_TYPES[headers[x_index]]:
                            return False, "Missing data"
                    else:
                        type = location_types[x_index]
                        tree_parent = Location.objects.get_or_create(name=cell_value[-1].strip(), type=type, tree_parent=tree_parent)[0]
                        if len(cell_value) ==2:
                            code = cell_value[0]
                            detail = type.details.all()[0]
                            if len(code)!= detail.length_of_code:
                                return False, "One or more %sCode is shorter than the required %d digits."%(type.name, detail.length_of_code)
                            LocationCode.objects.create(location=tree_parent, code=code)
                except IndexError:
                    continue
        return True, "Successfully uploaded"

    def remove_trailing(self,  name, in_array):
        return [header.replace(name,'') for header in in_array if header.endswith(name)]

    def regroup_with_code(self, row, group_size):
        new_row = []
        pos = 0
        for size in group_size:
            new_row.append(row[pos:pos+size])
            pos = pos+size
        return new_row

    def upload(self):
        location_types = []
        regroup_row = []
        headers, reader = self.csv_uploader.split_content()
        header_exists, message = self._get_location_type(headers, location_types, regroup_row)
        if not header_exists:
            return False, message
        type_headers = self.remove_trailing('Name', in_array=headers)
        return self._create_locations(reader, type_headers, location_types, regroup_row)