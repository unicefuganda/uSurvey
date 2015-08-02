from survey.models import Interviewer


class ExportInterviewersService:

    def __init__(self, export_fields):
        self.interviewers = Interviewer.objects.all()
        self.HEADERS = export_fields

    def formatted_responses(self):
        _formatted_responses = [','.join([entry.upper() for entry in self.HEADERS])]
        for interviewer in self.interviewers:
            info = interviewer.__dict__
            info['ussd'] = ','.join([access.user_identifier for access in interviewer.ussd_access])
            info['odk'] = ','.join([access.user_identifier for access in interviewer.odk_access])
            _formatted_responses.append(','.join(['"%s"'%str(info.get(entry, '')) for entry in self.HEADERS]))
        return _formatted_responses

