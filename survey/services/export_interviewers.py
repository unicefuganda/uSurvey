from survey.models import Interviewer


class ExportInterviewersService:

    def __init__(self, export_fields):
        self.interviewers = Interviewer.objects.all()
        self.HEADERS = export_fields

    def formatted_responses(self):
        _formatted_responses = [','.join([entry.upper() for entry in self.HEADERS])]
        for interviewer in self.interviewers:
            _formatted_responses.append(','.join(["%s"%str(interviewer.__dict__.get(entry, '')) for entry in self.HEADERS]))
        return _formatted_responses

