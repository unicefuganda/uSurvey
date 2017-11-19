from datetime import date
from survey.models.locations import *
from survey.models import Survey, Batch, Interviewer, Backend, \
    QuestionModule, Question, QuestionOption, EnumerationArea, \
    QuestionSet, ResponseValidation
from survey.services.results_download_service import ResultsDownloadService
from survey.tests.base_test import BaseTest


class ResultsDownloadServiceTest(BaseTest):

    def setUp(self):
        self.country = LocationType.objects.create(
            name='Country', slug='country')
        self.district = LocationType.objects.create(
            name='District', slug='district', parent=self.country)
        self.county = LocationType.objects.create(
            name='County', slug='county', parent=self.district)
        self.subcounty = LocationType.objects.create(
            name='Subcounty', slug='subcounty', parent=self.county)
        self.parish = LocationType.objects.create(
            name='Parish', slug='parish', parent=self.subcounty)
        self.village = LocationType.objects.create(
            name='Village', slug='village', parent=self.parish)
        uganda = Location.objects.create(name="Uganda", type=self.country)
        self.survey = Survey.objects.create(name='survey name', description='survey descrpition',
                                            sample_size=10)
        self.kampala = Location.objects.create(
            name="Kampala", type=self.district, parent=uganda)
        self.batch = Batch.objects.create(
            order=1, name="Batch A", survey=self.survey)
        backend = Backend.objects.create(name='something')
        self.ea = EnumerationArea.objects.create(name="EA")
        self.ea.locations.add(self.kampala)
        self.investigator = Interviewer.objects.create(name="Investigator",
                                                       ea=self.ea,
                                                       gender='1', level_of_education='Primary',
                                                       language='Eglish', weights=0)
        self.qset = QuestionSet.objects.create(name="Females")
        self.rsp = ResponseValidation.objects.create(validation_test="validationtest",
constraint_message="message")        
        module = QuestionModule.objects.create(name="Education")
        self.question_1 = Question.objects.create(identifier='1.11', text="This is a question11", answer_type='Numerical Answer',
                                                  qset_id=1, response_validation_id=1)
        self.question_2 = Question.objects.create(identifier='1.12', text="This is a question12", answer_type='Numerical Answer',
                                                  qset_id=1, response_validation_id=1)
        self.question_3 = Question.objects.create(identifier='1.13', text="This is a question13", answer_type='Numerical Answer',
                                                  qset_id=1, response_validation_id=1)
        self.yes_option = QuestionOption.objects.create(
            question=self.question_2, text="Yes", order=1)
        self.no_option = QuestionOption.objects.create(
            question=self.question_2, text="No", order=2)
