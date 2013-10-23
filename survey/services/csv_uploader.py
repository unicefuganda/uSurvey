
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

    def split_content(self):
        all_rows = self.file.readlines()
        headers = all_rows[0].strip().split(',')
        all_rows.remove(all_rows[0])
        data = [row.strip().split(',') for row in all_rows ]
        return headers, data

