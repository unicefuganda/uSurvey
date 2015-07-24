from django.core.management.base import BaseCommand, CommandError
# from rapidsms.contrib.locations.models import LocationType, Location
from survey.models.locations import Location, LocationType
from django.template.defaultfilters import slugify
import csv

class Command(BaseCommand):
    args = 'name_of_the_csv.file'
    help = 'Populates locations from a csv file'

    def handle(self, *args, **kwargs):
        csv_file = csv.reader(open(args[0],"rb"))
        headers = csv_file.next()
        location_types = []
        location_type = None
        for header in headers:
            header = header.strip().replace("Name", "").upper()
            location_type, _ = LocationType.objects.get_or_create(parent=location_type, name=header, slug=slugify(header))
            print 'loading ', location_type
            location_types.append(location_type)
        for items in csv_file:
            for index, item in enumerate(items):
                if index == 0:
                    location = None
                location, _ = Location.objects.get_or_create(name=item.strip(), type=location_types[index], parent=location)
                print 'loading ', location
        self.stdout.write('Successfully imported!')