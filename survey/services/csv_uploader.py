import csv

FIRST_LINE = 0


class CSVUploader:

    def __init__(self, file):
        self.file = file

    def file_is_not_csv(self):
        return '\0' in self.file.read()

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