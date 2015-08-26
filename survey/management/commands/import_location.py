from django.core.management.base import BaseCommand, CommandError
# from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Location, LocationType, EnumerationArea
from django.template.defaultfilters import slugify
import csv

class Command(BaseCommand):
    args = 'name_of_the_csv.file'
    help = 'Populates locations from a csv file'
    EA_INDEX = -2
    DEFAULT_TOTAL_HOUSEHOLDS = 1000
    TOTAL_EA_HOUSEHOLDS = -1
    def handle(self, *args, **kwargs):
        csv_file = csv.reader(open(args[0],"rb"))
        headers = csv_file.next()
        location_types = []
        location_type = None
        has_ea = False
        print 'ea index ', headers[self.EA_INDEX].strip()
        if headers[self.EA_INDEX].strip().replace("Name", "").upper() == 'EA':
            print 'poped ea'
            headers.pop(self.EA_INDEX) 
        for header in headers:
            header = header.strip().replace("Name", "").upper()
            location_type, _ = LocationType.objects.get_or_create(parent=location_type, name=header, slug=slugify(header))
            print 'loading ', location_type
            location_types.append(location_type)
        for items in csv_file:
            for index, item in enumerate(items):
                if index == 0:
                    location = None
                if has_ea and index == len(items) + self.EA_INDEX:
                    print 'loading EA ', item.strip()
                    ea = EnumerationArea.objects.get_or_create(name=item.strip(), 
                                                          total_location=DEFAULT_TOTAL_HOUSEHOLDS)
                    ea.locations.add(location)
                    ea.save()
                    break
                print 'loading item ', item
                location, _ = Location.objects.get_or_create(name=item.strip(), type=location_types[index], parent=location)
                print 'loading ', location
        self.stdout.write('Successfully imported!')