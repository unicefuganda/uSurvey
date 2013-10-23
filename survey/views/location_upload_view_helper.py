import csv
from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import LocationTypeDetails
from survey.services.csv_uploader import CSV_Uploader


class UploadLocation:
    def __init__(self,file):
        self.file = file
        self.REQUIRED_TYPES = {}
        self.csv_uploader = CSV_Uploader(self.file)

    def _get_location_type(self, headers, location_types):
        for header in headers:
            header = header.strip()
            location_type = LocationType.objects.filter(name=header, slug=slugify(header))

            if not location_type.exists():
                return False , 'Location type - %s not created' % header
            type = location_type[0]
            detail = type.details.all()
            if not detail:
                return False , 'Location type details for %s not found.'%header
            self.REQUIRED_TYPES[type.name] = detail[0].required
            location_types.append(type)
        return True,''

    def _create_locations(self, reader, headers, location_types):
        for row in reader:
            tree_parent = LocationTypeDetails.objects.all()[0].country
            for x_index, cell_value in enumerate(row):
                try:
                    if not cell_value:
                        if self.REQUIRED_TYPES[headers[x_index]]:
                            return False, "Missing data"
                    else:
                        tree_parent = Location.objects.get_or_create(name=cell_value.strip(), type=location_types[x_index], tree_parent=tree_parent)[0]
                except IndexError:
                    continue
        return True, "Successfully uploaded"

    def upload(self):
        location_types = []
        headers,reader = self.csv_uploader.split_content()
        header_exists, message = self._get_location_type(headers, location_types)
        if not header_exists:
            return False, message
        return self._create_locations(reader, headers, location_types)
