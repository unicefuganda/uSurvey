from django.http import HttpResponse
from rapidsms.contrib.locations.models import Location, LocationType
import json
from django.core.serializers.json import DjangoJSONEncoder

def children(request, location_id):
    location = Location.objects.get(id=location_id)
    children = location.get_children().values('id', 'name').order_by('name')
    json_dump = json.dumps(list(children), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, mimetype='application/json')