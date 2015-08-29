from django.template.defaultfilters import slugify
# from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import LocationTypeDetails, UploadErrorLog, Location, LocationType, EnumerationArea
from survey.services.csv_uploader import UploadService
from django.conf import settings


class UploadLocation(UploadService):
    MODEL = 'LOCATIONS'
    EA_INDEX = None

    def _get_location_types(self, headers):
        if headers[-2].lower().replace('name', '') == 'ea':
            self.EA_INDEX = len(headers) - 2
            headers.pop(self.EA_INDEX)
            headers.pop(self.EA_INDEX) #this is total households
        location_types = []
        map(lambda header: location_types.append(LocationType.objects.get(name__iexact=header, slug=slugify(header))), headers)
        return location_types

    def _create_locations(self, csv_rows, location_types):
        country = Location.objects.all().get(type__name__iexact='country')
        for index, row in enumerate(csv_rows):
            location = country
            for x_index, cell_value in enumerate(row):
                try:
                    if x_index == self.EA_INDEX:
                        ea, _ = EnumerationArea.objects.get_or_create(name=cell_value.strip(),
                                                              total_households=row[x_index + 1].strip() or
                                                                               settings.DEFAULT_TOTAL_HOUSEHOLDS_IN_EA)
                        ea.locations.add(location)
                        ea.save()
                        break
                    location, _ = Location.objects.get_or_create(name=cell_value.strip(), type=location_types[x_index], parent=location)
                except Exception, ex:
                    print 'could not load entry: ', x_index, ' reason ', str(ex)

    def upload(self):
        headers, rows = self.csv_uploader.split_content()
        cleaned_headers = self.remove_trailing('Name', in_array=headers, exclude='Code')
        if not cleaned_headers:
            UploadErrorLog.objects.create(model=self.MODEL, filename=self.file.name,
                                          error='Locations not uploaded. %s is not a valid csv file.' % self.file.name)
        else:
            location_types = self._get_location_types(cleaned_headers)
            self._create_locations(rows, location_types)
