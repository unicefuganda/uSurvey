from django.core.management.base import BaseCommand, CommandError
from survey.models import Location, LocationType, EnumerationArea
from django.template.defaultfilters import slugify
import csv, string
from django.db import transaction
from mptt.models import MPTTModel, TreeForeignKey
import datetime


class Command(BaseCommand):
    args = 'name_of_the_csv.file'
    help = 'Populates locations from a csv file'

    # @transaction.commit_on_success
    def handle(self, *args, **kwargs):
        print datetime.datetime.now(),"start"
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
            #self.stdout.write('loading %s' % header)
            location_type, created = LocationType.objects.get_or_create(name=header, slug=slugify(header),
                                                                        parent=location_type)
            location_types.append(location_type)
        total_divisions = len(location_types)
        count = 0
        country = None
        for row in csv_file:
            parent = None
            if len(row) < total_divisions:
                print 'skiping entry... ', row
                continue
            else:
                if len(row) > total_divisions:
                    ea_name = row.pop(-1)
                row = row[:total_divisions]

            with transaction.atomic():
                with Location.tree.disable_mptt_updates():
                    for index, col in enumerate(row):
                        loc_name = string.capwords(col.strip())
                        loc_type = location_types[index]
                        parent, _ = Location.objects.get_or_create(name=loc_name, type=loc_type, parent=parent)
                    if has_ea:
                        if parent:
                            ea, created = EnumerationArea.objects.get_or_create(name=ea_name, code='%s-%s'%(parent.pk, ea_name))
                            if created:
                                ea.locations.add(parent)
            count = count + 1
            if count % 1000 == 0:
                print 'loaded up to entry...' , row
        #clean up... delete locations and types having no name
        Location.tree.rebuild()
        LocationType.objects.filter(name='').delete()
        Location.objects.filter(name='').delete()
        EnumerationArea.objects.filter(name='').delete()
        print datetime.datetime.now(),"completed"
        self.stdout.write('Successfully imported!')
