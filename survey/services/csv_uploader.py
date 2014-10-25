import csv
from datetime import datetime, timedelta
from django.utils.timezone import utc
from survey.models import UploadErrorLog

from survey.investigator_configs import UPLOAD_ERROR_LOG_EXPIRY


FIRST_LINE = 0


class CSVUploader:

    def __init__(self, file):
        self.file = file

    def file_is_not_csv(self):
        return '\0' in self.file.read()

    def headers(self):
        return csv.reader(self.file).next()

    def split_content(self):
        if self.file_is_not_csv():
            return [], []
        self.read_file_from_begging()
        csv_file = csv.reader(self.file)
        all_rows = [row for row in csv_file]
        headers = all_rows[FIRST_LINE]
        all_rows.pop(FIRST_LINE)
        return headers, all_rows

    def read_file_from_begging(self):
        self.file.seek(FIRST_LINE)


class UploadService(object):
    MODEL = None

    def __init__(self, _file):
        self.file = _file
        self.csv_uploader = CSVUploader(self.file)
        self.clean_db()

    def clean_db(self):
        one_month_before_today = datetime.utcnow().replace(tzinfo=utc) - timedelta(days=UPLOAD_ERROR_LOG_EXPIRY)
        all_entries_before_one_month = UploadErrorLog.objects.filter(model=self.MODEL, created__lte=one_month_before_today)
        all_entries_before_one_month.delete()

    def log_error(self, row_number, error):
        UploadErrorLog.objects.create(model=self.MODEL, filename=self.file.name[:19], row_number=row_number, error=error)

    @staticmethod
    def remove_trailing(name, in_array, exclude=None):
        new_array = [header.replace(name, '') for header in in_array]
        if exclude:
            new_array = filter(lambda element : not element.endswith(exclude), new_array)
        return new_array
