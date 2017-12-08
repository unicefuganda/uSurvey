from django.core.management.base import BaseCommand
from survey.models import LocationType, Location, EnumerationArea


class Command(BaseCommand):
    help = 'This commands clears all the Location and Enumeration Area data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Cleaning Enumeration Areas...')
        EnumerationArea.objects.all().delete()
        self.stdout.write('Cleaning Locations...')
        Location.objects.all().delete()
        LocationType.objects.all().delete()
        self.stdout.write('Cleaning completed!')
