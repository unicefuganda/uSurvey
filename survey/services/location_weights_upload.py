from django.utils.timezone import utc
from survey.models import LocationWeight, UploadErrorLog, Location
from survey.services.csv_uploader import UploadService
from survey.models.locations import *

class UploadLocationWeights(UploadService):
    MODEL = 'WEIGHTS'

    @classmethod
    def parents_locations_match(cls, location, given_parents):
        location_parents = location.get_ancestors().values_list('name', flat=True)
        check = [parent_name in location_parents for parent_name in given_parents]
        return check.count(True) == len(given_parents)

    def check_location_errors(self, index, row, headers):
        lowest_location = row[-2]
        location = Location.objects.filter(name=lowest_location, parent__name__iexact=row[-3].lower())
        if not location.exists():
            self.log_error(index+1, 'There is no %s with name: %s, in %s.' % (headers[-2].lower(), row[-2], row[-3]))
            return
        if not self.parents_locations_match(location[0], row[:-3]):
            self.log_error(index+1, 'The location hierarchy %s does not exist.' % ((' >> '.join(row[:-1]))))
            return
        return location

    def save_weight(self, index, row, location, survey):
        try:
            LocationWeight.objects.create(location=location[0], selection_probability=float(row[-1]), survey=survey)
        except ValueError, e:
            self.log_error(index+1, 'Selection probability must be a number.')

    def create_locations_weights(self, reader, headers, survey):
        for index, row in enumerate(reader):
            location = self.check_location_errors(index, row, headers)
            if location:
                self.save_weight(index, row, location, survey)

    def upload(self, survey):
        headers, reader = self.csv_uploader.split_content()
        cleaned_headers = self.remove_trailing('Name', in_array=headers)
        if not cleaned_headers:
            UploadErrorLog.objects.create(model=self.MODEL, filename=self.file.name,
                                          error='Location weights not uploaded. %s is not a valid csv file.' % self.file.name)
        else:
            self.create_locations_weights(reader, cleaned_headers, survey)
