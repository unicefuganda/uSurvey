from django.core.management.base import BaseCommand, CommandError
from rapidsms.contrib.locations.models import Location, LocationType
from django.template.defaultfilters import slugify
import csv

class Command(BaseCommand):
    args = 'name_of_the_csv.file'
    help = 'Populates locations from a csv file'

    def handle(self, *args, **kwargs):
        csv_file = csv.reader(open(args[0],"rb"))
        headers = csv_file.next()
        location_types = []
        for header in headers:
            header = header.strip()
            location_types.append(LocationType.objects.create(name=header,slug=slugify(header)))
        for items in csv_file:
            tree_parent = None
            for index, item in enumerate(items):
                tree_parent = Location.objects.get_or_create(name=item.strip(), type=location_types[index], tree_parent=tree_parent)[0]
        self.stdout.write('Successfully imported!')