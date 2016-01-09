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
        #existing_eas = EnumerationArea.objects.all()
        #existing_eas = dict([(str(ea.locations.all()[0].pk), ea.name) for ea in existing_eas if ea.locations.count()])
        #treated_locs = dict([((string.capwords(loc.name), loc.type.pk, loc.parent.pk), loc)
        #                     for loc in Location.objects.exclude(parent__isnull=True)])
        total_divisions = len(location_types)
        count = 0
        country = None
        for row in csv_file:
            parent = None
            if len(row) < total_divisions:
                self.stdout.write('skiping entry... %s' % row)
                continue
            else:
                if len(row) > total_divisions:
                    ea_name = row.pop(-1)
                row = row[:total_divisions]
            self.stdout.write('loading entry... %s' % row)
            for index, col in enumerate(row):
                loc_name = string.capwords(col.strip())
                loc_type = location_types[index]
                # if parent:
                #     location = treated_locs.get((loc_name, loc_type.pk, parent.pk), None)
                #     if location is None:
                #         location = Location.objects.create(name=loc_name, type=loc_type, parent=parent)
                #         treated_locs[(loc_name, loc_type.pk, parent.pk)] = location
                #     parent = location
                # else:
                #     if country is None:
                #         country, _ = Location.objects.get_or_create(name=col,type=loc_type,parent=parent)
                #     parent = country
                parent, _ = Location.objects.get_or_create(name=loc_name, type=loc_type, parent=parent)
                # if parent and loc_name != string.capwords(country.name):
                #     parent_id = str(parent.pk)
                #     print 'parent: ', parent.name, ' item: ', item, ' parentpk ', parent_id
                #     location = treated_locs.get((parent_id ,loc_name), None)
                #     if location is None:
                #         location = Location.objects.create(name=loc_name, type=loc_type, parent=parent)
                #     treated_locs[(parent_id, loc_name)] = location
                #     parent = location
                #     # if len(treated_locs) == 10:
                #     #     import pdb; pdb.set_trace()
                #     print 'new loc is ', parent.name, 'now pk is ', parent.pk
                # else:
                #     print 'fetching country code: ', item, 'parent ', parent
                #     if country is None:
                #         country, _ = Location.objects.get_or_create(name=item,type=loc_type,parent=parent)
                #     # parent_name = string.capwords(country.name)
                #     parent = country
                #     print 'no fetchicing happened'


                # parent, created = Location.objects.get_or_create(name=item.strip(), type=loc_type, parent=parent)
            if has_ea:
                if parent:
                    # ea = existing_eas.get((str(parent.pk), ea_name),  EnumerationArea.objects.create(name=ea_name,
                    #                                                             code='%s-%s'%(parent.pk, ea_name)))
                    ea, created = EnumerationArea.objects.get_or_create(name=ea_name, code='%s-%s'%(parent.pk, ea_name))
                    # print 'creating ea: ', parent.name, 'ea: ', ea_name, ' parentpk ', parent.pk
                    if created:
                        ea.locations.add(parent)
                    # existing_eas[(str(parent.pk), ea_name)] = ea
            count = count + 1
            if not count%1000:
                self.stdout.write('>>treating entry %s - %s' % (count, row))
        #clean up... delete locations and types having no name
        LocationType.objects.filter(name='').delete()
        Location.objects.filter(name='').delete()
        EnumerationArea.objects.filter(name='').delete()
        self.stdout.write('Successfully imported!')