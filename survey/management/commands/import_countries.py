from django.core.management.base import BaseCommand, CommandError
from rapidsms.contrib.locations.models import Location, LocationType
from django.template.defaultfilters import slugify
import csv

class Command(BaseCommand):
    args = 'name_of_the_csv.file'
    help = 'Populates locations from a csv file'

    def handle(self, *args, **kwargs):
        csv_file = csv.reader(open(args[0],"rb"))
        country , created = LocationType.objects.get_or_create(name='Country',slug=slugify('country'))
        for items in csv_file:
            tree_parent = None
            for index, item in enumerate(items):
                Location.objects.get_or_create(name=item.strip(), type=country, tree_parent=tree_parent)
        self.stdout.write('Successfully imported!')