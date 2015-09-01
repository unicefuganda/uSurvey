from django.core.management.base import BaseCommand, CommandError
# from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Location, LocationType, EnumerationArea
from django.template.defaultfilters import slugify
import csv

class Command(BaseCommand):
    args = 'name_of_the_csv.file'
    help = 'Populates locations from a csv file'
    EA_INDEX = 6
    DEFAULT_TOTAL_HOUSEHOLDS = 1000
    def handle(self, *args, **kwargs):
        csv_file = csv.reader(open(args[0],"rb"))
        headers = csv_file.next()
        location_types = []
        location_type = None
        has_ea = False

        print 'ea index ', headers[self.EA_INDEX].strip()
        if headers[self.EA_INDEX].strip().replace("Name", "").upper() == 'EA':
            headers.pop(self.EA_INDEX)
            headers.pop(self.EA_INDEX)
            has_ea = True
        for header in headers:
            header = header.strip().replace("Name", "").upper()
            location_type, _ = LocationType.objects.get_or_create(parent=location_type, name=header, slug=slugify(header))
            print 'loading ', location_type
            location_types.append(location_type)
        existing_locs = dict([((loc.name, loc.type.pk, loc.parent.pk), loc) for loc in Location.objects.all() if loc.parent])
        existing_eas = dict([(ea.name, ea) for ea in EnumerationArea.objects.all()])
        print 'starting with ', len(existing_locs), ' existing locations'
        print 'starting with ', len(existing_eas), ' existing eas'
        for items in csv_file:
            for index, item in enumerate(items):
                if index == 0:
                    location = None
                print 'treating item ', item
                if has_ea and index == self.EA_INDEX:
                    print 'loading EA ', item.strip()
                    # ea = existing_eas.get(item.strip(), None)
                    # if ea is None: #not already created
                    ea, _ = EnumerationArea.objects.get_or_create(name=item.strip(),
                                                total_households=self.DEFAULT_TOTAL_HOUSEHOLDS)
                    ea.locations.add(location)
                    ea.save()
                    print 'added ea ', item
                    print len(existing_eas), ' eas now'
                    existing_eas[item.strip()] = ea
                    break

                parent = location
                # if parent is None:
                #     location, _ = Location.objects.get_or_create(name=item.strip(), type=location_types[index], parent=parent)
                # else:
                #     location = existing_locs.get((item.strip(),location_types[index].pk, parent.pk), None)#check if exsiting
                #     if location is None:
                location, _ = Location.objects.get_or_create(name=item.strip(),
                                                          type=location_types[index], parent=parent)
                # existing_locs[(item.strip(),location_types[index].pk, parent.pk)] = location
                # print 'loading ', location
                # print len(existing_locs), ' locations now'
        #clean up... delete locations and types having no name
        LocationType.objects.filter(name='').delete()
        Location.objects.filter(name='').delete()
        EnumerationArea.objects.filter(name='').delete()
        self.stdout.write('Successfully imported!')
