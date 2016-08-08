import json

from django.http import HttpResponse
# from rapidsms.contrib.locations.models import Location
from survey.models.locations import *
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from survey.models import EnumerationArea
from survey.views.location_widget import LocationWidget


@login_required
def children(request, location_id):
    location = Location.objects.get(id=location_id)
    children = location.get_children().values('id', 'name').order_by('name')
    json_dump = json.dumps(list(children), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')


def enumeration_areas(request, location_id):
    location = Location.objects.get(id=location_id)
    eas = EnumerationArea.under_(location).values('id', 'name').order_by('name')
    json_dump = json.dumps(list(eas), cls=DjangoJSONEncoder)
    return HttpResponse(json_dump, content_type='application/json')
