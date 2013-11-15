from mock import patch

from survey.forms.upload_csv_file import UploadWeightsForm
from survey.tasks import upload_task
from survey.tests.base_test import BaseTest


class UploadTaskTest(BaseTest):

    @patch('survey.forms.upload_csv_file.UploadWeightsForm.upload')
    def test_should_call_upload_on_upload_form(self, mock_upload):
        mock_upload.return_value =(True, 'some message')
        upload_form = UploadWeightsForm()
        task_result = upload_task.delay(upload_form)
        status, message = task_result.get()
        self.assertTrue(status)
        self.assertEqual('some message', message)
        self.assertTrue(task_result.successful())
