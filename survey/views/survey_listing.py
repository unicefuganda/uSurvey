import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from survey.interviewer_configs import *
from survey.models import ListingTemplate, Batch

@permission_required('auth.can_view_batches')
def sampling_criteria(request, id):
    listing_template = get_object_or_404(ListingTemplate, pk=id)



