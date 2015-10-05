from django.core.management.base import BaseCommand, CommandError
# from rapidsms.contrib.locations.models import LocationType, Location
from survey.models import Location, LocationType, EnumerationArea
from django.template.defaultfilters import slugify
import csv

# class Command(BaseCommand):
#     args = 'name_of_the_csv.file'
#     help = 'Populates locations from a csv file'
#     EA_INDEX = 6
#     DEFAULT_TOTAL_HOUSEHOLDS = 1000
#     def handle(self, *args, **kwargs):
#         csv_file = csv.reader(open(args[0],"rb"))
#         headers = csv_file.next()
#         location_types = []
#         location_type = None
#         has_ea = False
#
#         print 'ea index ', headers[self.EA_INDEX].strip()
#         if headers[self.EA_INDEX].strip().replace("Name", "").upper() == 'EA':
#             headers.pop(self.EA_INDEX)
#             headers.pop(self.EA_INDEX)
#             has_ea = True
#         for header in headers:
#             if header.strip():
#                 header = header.strip().replace("Name", "").upper()
#                 location_type, _ = LocationType.objects.get_or_create(parent=location_type, name=header, slug=slugify(header))
#                 print 'loading ', location_type
#                 location_types.append(location_type)
#         existing_locs = dict([((loc.name, loc.parent.name), loc) for loc in Location.objects.all() if loc.parent])
#         existing_eas = dict([((ea.name, ea.locations.all()[0].parent.name), ea) for ea in EnumerationArea.objects.all() if ea.locations.exists()])
#         for items in csv_file:
#             for index, item in enumerate(items):
#                 if index == 0:
#                     location = None
#                 print 'treating item ', item
#                 parent = location
#                 if parent is None:
#                     location, _ = Location.objects.get_or_create(name=item.strip(), type=location_types[index], parent=parent)
#                 else:
#                     print 'index is', index
#                     print 'loctypes ', len(location_types)
#                     if index < self.EA_INDEX:
#                         location = existing_locs.get((item.strip(), parent.name), None)#check if exsiting
#                         print 'loc exists', location_types[index]
#                         if location is None:
#                             Location.objects.create(name=item.strip(),
#                                                               type=location_types[index], parent=parent)
#                     else:
#                         print 'loading EA ', item.strip()
#                         ea = existing_eas.get((item.strip(), parent.name), None)
#                         if ea is None: #not already created
#                             ea = EnumerationArea.objects.create(name=item.strip())
#                             ea.locations.add(location)
#                             #ea.save()
#                         #print 'added ea ', item
#                         #existing_eas[item.strip()] = ea
#                         break
#                 # existing_locs[(item.strip(),location_types[index].pk, parent.pk)] = location
#                 # print 'loading ', location
#                 # print len(existing_locs), ' locations now'
#         #clean up... delete locations and types having no name
#         LocationType.objects.filter(name='').delete()
#         Location.objects.filter(name='').delete()
#         EnumerationArea.objects.filter(name='').delete()
#         self.stdout.write('Successfully imported!')



class Command(BaseCommand):
    args = 'name_of_the_csv.file'
    help = 'Populates locations from a csv file'

    def handle(self, *args, **kwargs):
        csv_file = csv.reader(open(args[0],"rb"))
        headers = csv_file.next()
        location_types = []
        ea_index = 6
        location_type = None
        for idx, header in enumerate(headers):
            if idx == ea_index:
                break
            header = header.strip().replace("Name", "")
            print 'creating ', header
            location_type, created = LocationType.objects.get_or_create(name=header, slug=slugify(header), parent=location_type)
            location_types.append(location_type)
        for items in csv_file:
            parent = None
            for index, item in enumerate(items):
                print 'loading ', item
                if index == ea_index:
                    ea = EnumerationArea.objects.create(name=item.strip())
                    ea.locations.add(parent)
                    ea.save()
                    break
                if index != ea_index:
                    parent = Location.objects.get_or_create(name=item.strip(), type=location_types[index], parent=parent)[0]


        self.stdout.write('Successfully imported!')