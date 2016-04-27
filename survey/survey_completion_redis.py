import os
import sys
import redis
script_dir = os.path.abspath(os.path.dirname(__file__))
project_dir = os.path.abspath(os.path.dirname(script_dir))

sys.path.append(project_dir)
sys.path.append(os.path.dirname(project_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mics.settings")
import django
django.setup()

from survey.models import Survey, Interviewer, LocationType
from survey.services.completion_rates_calculator import BatchLocationCompletionRates,\
    BatchHighLevelLocationsCompletionRates, BatchSurveyCompletionRates
import json
from django.core.serializers.json import DjangoJSONEncoder

def add_to_redis():
    r_server = redis.Redis('localhost')
    survey_all = Survey.objects.all().values_list("id")
    for id in survey_all:
        survey = Survey.objects.get(id=id[0])
        location_type = LocationType.largest_unit()
        completion_rates = BatchSurveyCompletionRates(location_type).get_completion_formatted_for_json(survey)
        json_dump = json.dumps(completion_rates, cls=DjangoJSONEncoder)
        r_server.set(id[0], json_dump)

if __name__ == "__main__":
    add_to_redis()