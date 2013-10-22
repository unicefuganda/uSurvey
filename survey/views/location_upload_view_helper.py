import csv
from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import LocationType, Location

class UploadLocation:
    def __init__(self,file):
        self.file = file

    def upload(self):
        with open(self.file, 'rb') as csv_file:
            location_types = []
            reader = csv.reader(csv_file)
            headers = reader.next()
            for header in headers:
                header = header.strip()
                location_type = LocationType.objects.filter(name=header, slug=slugify(header))
                if location_type.exists():
                    location_types.append(location_type[0])
                else:
                    message = "Location type - %s not created" % header
                    return False, message
            for row in reader:
                tree_parent = None
                for index, item in enumerate(row):
                    tree_parent = Location.objects.get_or_create(name=item.strip(), type=location_types[index], tree_parent=tree_parent)[0]
                    message = "Successfully uploaded"
            return True,message