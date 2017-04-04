import os
from lxml import etree
import mimetypes
from django.conf import settings
from django.db import models
from survey.models.base import BaseModel
from survey.models.interviewer import Interviewer
from survey.models.surveys import Survey
from survey.models.enumeration_area import EnumerationArea
from survey.models.questions import QuestionSet


class ODKFileDownload(BaseModel):
    assignments = models.ManyToManyField('SurveyAllocation', related_name='file_downloads')


class ODKSubmission(BaseModel):
    STARTED = 1
    COMPLETED = 2
    interviewer = models.ForeignKey(
        Interviewer, related_name="odk_submissions")
    survey = models.ForeignKey(Survey, related_name="odk_submissions")
    ea = models.ForeignKey(EnumerationArea, related_name="odk_submissions",null=True, blank=True)
    question_set = models.ForeignKey(QuestionSet, related_name='odk_submissions',null=True, blank=True)
    form_id = models.CharField(max_length=256)
    description = models.CharField(max_length=256, null=True, blank=True)
    instance_id = models.CharField(max_length=256)
    instance_name = models.CharField(max_length=256, null=True, blank=True)
    xml = models.TextField()
    status = models.IntegerField(choices=[( STARTED, 'Started'), (COMPLETED, 'Completed')], default=STARTED)
    # this keeps track of all interviews entries created as a result of this submisssion
    interviews = models.ManyToManyField('Interview', related_name='odk_submissions')

    class Meta:
        app_label = 'survey'

    def has_attachments(self):
        return self.attachments.count() > 0

    def save_attachments(self, media_files):
        for f in media_files.values():
            content_type = f.content_type if hasattr(f, 'content_type') else ''
            attach, created = Attachment.objects.get_or_create(submission=self,
                                                               media_file=f,
                                                               mimetype=content_type)

    def update_submission(self):
        tree = etree.fromstring(self.xml)
        try:
            submissions_node = tree.xpath('//qset/submissions')[0]
        except IndexError:
            submissions_node = etree.Element('submissions')
            tree.insert(0, submissions_node)
        try:
            submission_id_nodes = tree.xpath('//qset/submissions/id')[0]
        except IndexError:
            submission_id_node = etree.Element('id')
            submissions_node.insert(0, submission_id_node)
        submission_id_node.text = str(self.id)
        try:
            dates_node = tree.xpath('//qset/submissions/dates')[0]
        except IndexError:
            dates_node = etree.Element('dates')
            submissions_node.insert(0, dates_node)
        last_modified_node = etree.Element('lastModified')
        last_modified_node.text = str(self.modified)
        dates_node.insert(0, last_modified_node)
        self.xml = etree.tostring(tree)

    def save(self, *args, **kwargs):
        if self.pk:
            self.update_submission()
        return super(ODKSubmission, self).save(*args, **kwargs)



def upload_to(attachment, filename):
    return os.path.join(
        settings.SUBMISSION_UPLOAD_BASE,
        attachment.submission.pk,
        'attachments',
        os.path.basename(filename))


class Attachment(BaseModel):
    submission = models.ForeignKey(ODKSubmission, related_name="attachments")
    media_file = models.FileField(upload_to=upload_to)
    mimetype = models.CharField(
        max_length=50, null=False, blank=True, default='')

    class Meta:
        app_label = 'survey'

    def save(self, *args, **kwargs):
        if self.media_file and self.mimetype == '':
            # guess mimetype
            mimetype, encoding = mimetypes.guess_type(self.media_file.name)
            if mimetype:
                self.mimetype = mimetype
        super(Attachment, self).save(*args, **kwargs)
