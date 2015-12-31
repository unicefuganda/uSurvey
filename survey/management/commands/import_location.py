from django.core.management.base import BaseCommand, CommandError
from survey.models import Location, LocationType, EnumerationArea
from django.template.defaultfilters import slugify
import csv, string
from django.db import transaction


class Command(BaseCommand):
    args = 'name_of_the_csv.file'
    help = 'Populates locations from a csv file'

    # @transaction.commit_on_success
    def handle(self, *args, **kwargs):
        csv_file = csv.reader(open(args[0],"rb"))
        headers = csv_file.next()
        location_types = []
        last_entry_empty = False
        if not headers[-1].strip():
            headers.pop(-1)
            last_entry_empty = True
        has_ea = False
        if headers[-1].lower().replace('name', '') == 'ea':
            has_ea = True
            headers.pop(-1)
        location_type = None
        for idx, header in enumerate(headers):
            header = string.capwords(header.strip().replace("Name", ""))
            self.stdout.write('loading %s' % header)
            location_type, created = LocationType.objects.get_or_create(name=header, slug=slugify(header),
                                                                        parent=location_type)
            location_types.append(location_type)
        existing_eas = EnumerationArea.objects.all()
        existing_eas = [ea.code for ea in existing_eas]
        treated_locs = {}
        total_divisions = len(location_types)
        count = 0
        for items in csv_file:
            parent = None
            if len(items) <= total_divisions:
                self.stdout.write('skiping entry... %s' % items)
                continue
            else:
                items = items[:total_divisions+1]
            # self.stdout.write('loading entry... %s' % items)
            if has_ea:
                ea_name = items.pop(-1)
            for index, item in enumerate(items):
                item = string.capwords(item.strip())
                loc_type = location_types[index]
                parent, created = Location.objects.get_or_create(name=item.strip(), type=loc_type, parent=parent)
            if has_ea:
                if parent and unicode(parent.pk) not in existing_eas:
                    ea, created = EnumerationArea.objects.get_or_create(name=ea_name, code=parent.pk)
                    ea.locations.add(parent)
            count = count + 1
            if not count%1000:
                self.stdout.write('>>treating entry %s - %s' % (count, items))
        #clean up... delete locations and types having no name
        LocationType.objects.filter(name='').delete()
        Location.objects.filter(name='').delete()
        EnumerationArea.objects.filter(name='').delete()
        self.stdout.write('Successfully imported!')