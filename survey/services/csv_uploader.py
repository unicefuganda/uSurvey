import csv
class CSV_Uploader:

    def __init__(self, file):
        self.file = file

    def headers(self):
        return self.file.readline().strip().split(',')

    def rows(self):
        all_rows =  self.file.readlines()
        data = all_rows.remove()
        all_rows = self.file.readlines()[0].split('\r')
        print all_rows
        return [row.split(',') for row in all_rows]

    def xsplit_content(self):
        if self.file_is_not_csv():
            return [],[]
        self.read_file_from_beginging()

        all_rows = self.file.readlines()
        headers = all_rows[0].strip().split(',')
        all_rows.remove(all_rows[0])
        data = [row.strip().split(',') for row in all_rows ]
        return headers, data

    def file_is_not_csv(self):
        return '\0' in self.file.read()

    def split_content(self):
        if self.file_is_not_csv():
            return [],[]
        self.read_file_from_beginging()
        csv_file = csv.reader(self.file)
        all_rows = [row for row in csv_file]
        headers = all_rows[0]
        all_rows.pop(0)
        return headers, all_rows

    def read_file_from_beginging(self):
        self.file.seek(0)
