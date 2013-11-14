from rapidsms.contrib.locations.models import Location
from survey.models import LocationWeight
from survey.services.csv_uploader import CSVUploader


class UploadLocationWeights:
    REQUIRED_TYPES = {}

    def __init__(self, _file):
        self.file = _file
        self.csv_uploader = CSVUploader(self.file)

    @classmethod
    def parents_locations_match(cls, location, parents):
        check = [parent_name in location.get_ancestors().values_list('name', flat=True) for parent_name in parents]
        return check.count(True) == len(parents)


    @classmethod
    def create_locations_weights(cls, reader, headers, survey):
        for index, row in enumerate(reader):
            lowest_location = row[-2]
            location = Location.objects.filter(name=lowest_location, tree_parent__name__iexact=row[-3].lower())
            if not location.exists():
                    return False, 'There is no %s with name: %s, in %s.' % (headers[-2], row[-2], row[-3])

            if not cls.parents_locations_match(location[0], row[:-3]):
                return False, 'The location hierarchy %s does not exist.' % ((' >> '.join(row[:-1])))

            try:
                LocationWeight.objects.create(location=location[0], selection_probability=float(row[-1]), survey=survey)
            except ValueError, e:
                return False, 'Selection probability must be a number.'

        return True, 'Location weights successfully uploaded.'

    @staticmethod
    def remove_trailing(name, in_array):
        return [header.replace(name, '').lower() for header in in_array]

    def upload(self, survey):
        headers, reader = self.csv_uploader.split_content()
        cleaned_headers = self.remove_trailing('Name', in_array=headers)
        if not cleaned_headers:
            return False, 'Location weights not uploaded. %s is not a csv file.' % self.file.name
        success, message = self.create_locations_weights(reader, cleaned_headers, survey)
        if not success:
            message = 'Location weights not uploaded. ' + message
        return success, message