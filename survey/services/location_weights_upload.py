from datetime import datetime, timedelta
from django.utils.timezone import utc
from rapidsms.contrib.locations.models import Location
from survey.models import LocationWeight, UploadErrorLog
from survey.services.csv_uploader import CSVUploader


class UploadLocationWeights:
    MODEL = 'WEIGHTS'

    def __init__(self, _file):
        self.file = _file
        self.csv_uploader = CSVUploader(self.file)
        self.clean_db()

    def clean_db(self):
        one_month_before_today = datetime.utcnow().replace(tzinfo=utc) - timedelta(days=30)
        all_entries_before_one_month = UploadErrorLog.objects.filter(model=self.MODEL, created__lte=one_month_before_today)
        all_entries_before_one_month.delete()

    @classmethod
    def parents_locations_match(cls, location, parents):
        check = [parent_name in location.get_ancestors().values_list('name', flat=True) for parent_name in parents]
        return check.count(True) == len(parents)

    def log_error(self, row_number, error):
        UploadErrorLog.objects.create(model=self.MODEL, filename=self.file.name, row_number=row_number, error=error)

    def check_location_errors(self, index, row, headers):
        lowest_location = row[-2]
        location = Location.objects.filter(name=lowest_location, tree_parent__name__iexact=row[-3].lower())
        if not location.exists():
            self.log_error(index+1, 'There is no %s with name: %s, in %s.' % (headers[-2], row[-2], row[-3]))
            return
        if not self.parents_locations_match(location[0], row[:-3]):
            self.log_error(index+1, 'The location hierarchy %s does not exist.' % ((' >> '.join(row[:-1]))))
            return
        return location

    def save_weight(self, index, row, location, survey):
        try:
            LocationWeight.objects.create(location=location[0], selection_probability=float(row[-1]), survey=survey)
        except ValueError, e:
            self.log_error(index+1,'Selection probability must be a number.')

    def create_locations_weights(self, reader, headers, survey):
        for index, row in enumerate(reader):
            location = self.check_location_errors(index, row, headers)
            if location:
                self.save_weight(index, row, location, survey)

    @staticmethod
    def remove_trailing(name, in_array):
        return [header.replace(name, '').lower() for header in in_array]

    def upload(self, survey):
        headers, reader = self.csv_uploader.split_content()
        cleaned_headers = self.remove_trailing('Name', in_array=headers)
        if not cleaned_headers:
            UploadErrorLog.objects.create(model=self.MODEL, filename=self.file.name,
                                          error='Location weights not uploaded. %s is not a csv file.' % self.file.name)
        self.create_locations_weights(reader, cleaned_headers, survey)