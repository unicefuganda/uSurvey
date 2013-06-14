from django.test import TestCase
from survey.models import *
from django.db import IntegrityError
from rapidsms.contrib.locations.models import Location, LocationType


class InvestigatorTest(TestCase):

    def test_fields(self):
        investigator = Investigator()
        fields = [str(item.attname) for item in investigator._meta.fields]
        self.assertEqual(len(fields), 10)
        for field in ['id', 'name', 'mobile_number', 'created', 'modified', 'male', 'age', 'level_of_education', 'location_id', 'language']:
            self.assertIn(field, fields)

    def test_store(self):
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210")
        self.failUnless(investigator.id)
        self.failUnless(investigator.created)
        self.failUnless(investigator.modified)

    def test_validations(self):
        Investigator.objects.create(name="", mobile_number = "mobile_number")
        self.failUnlessRaises(IntegrityError, Investigator.objects.create, mobile_number = "mobile_number")

class LocationTest(TestCase):

    def test_store(self):
        country = LocationType.objects.create(name='Country',slug='country')
        district = LocationType.objects.create(name='District',slug='district')
        uganda = Location.objects.create(name="Uganda", type=country)
        kampala = Location.objects.create(name="Kampala", type=district, tree_parent=uganda)

        u = Location.objects.get(type__name='Country',name='Uganda')
        report_locations = u.get_descendants(include_self=True).all()
        self.assertEqual(len(report_locations), 2)
        self.assertIn(uganda, report_locations)
        self.assertIn(kampala, report_locations)

class LocationAutoCompleteTest(TestCase):
    def test_store(self):
        self.assertEqual(len(LocationAutoComplete.objects.all()), 0)
        uganda = Location.objects.create(name="Uganda")
        self.assertEqual(len(LocationAutoComplete.objects.all()), 1)
        self.assertEqual(uganda.auto_complete_text(), "Uganda")
        self.assertEqual(LocationAutoComplete.objects.all()[0].text, "Uganda")

        kampala = Location.objects.create(name="Kampala", tree_parent=uganda)
        self.assertEqual(kampala.auto_complete_text(), "Kampala, Uganda")

        soroti = Location.objects.create(name="Soroti", tree_parent=kampala)
        self.assertEqual(soroti.auto_complete_text(), "Soroti, Kampala, Uganda")

        kampala.name = "Kampala Changed"
        kampala.save()
        self.assertEqual(kampala.auto_complete_text(), "Kampala Changed, Uganda")

        soroti = Location.objects.get(name="Soroti")
        self.assertEqual(soroti.auto_complete_text(), "Soroti, Kampala Changed, Uganda")

class SurveyTest(TestCase):
    def test_store(self):
        survey = Survey.objects.create(name='Survey Name', description='Survey description')
        self.failUnless(survey.id)

class BatchTest(TestCase):
    def test_store(self):
        survey = Survey.objects.create(name='Survey Name', description='Survey description')
        batch = Batch.objects.create(survey=survey)
        self.failUnless(batch.id)

class IndicatorTest(TestCase):
    def setUp(self):
        survey = Survey.objects.create(name='Survey Name', description='Survey description')
        self.batch = Batch.objects.create(survey=survey)

    def test_store(self):
        indicator = Indicator.objects.create(batch=self.batch)
        self.failUnless(indicator.id)

    def test_order(self):
        indicator_2 = Indicator.objects.create(batch=self.batch, order=2)
        indicator_1 = Indicator.objects.create(batch=self.batch, order=1)
        indicators = self.batch.indicators.order_by('order').all()
        self.assertEqual(indicators[0], indicator_1)
        self.assertEqual(indicators[1], indicator_2)

class QuestionTest(TestCase):
    def setUp(self):
        survey = Survey.objects.create(name='Survey Name', description='Survey description')
        batch = Batch.objects.create(survey=survey)
        self.indicator = Indicator.objects.create(batch=batch)

    def test_numerical_question(self):
        question = Question.objects.create(indicator=self.indicator, text="This is a question", answer_type=Question.NUMBER)
        self.failUnless(question.id)

    def test_text_question(self):
        question = Question.objects.create(indicator=self.indicator, text="This is a question", answer_type=Question.TEXT)
        self.failUnless(question.id)

    def test_multichoice_question(self):
        question = Question.objects.create(indicator=self.indicator, text="This is a question", answer_type=Question.MULTICHOICE)
        self.failUnless(question.id)

    def test_order(self):
        question_2 = Question.objects.create(indicator=self.indicator, text="This is a question", answer_type="number", order=2)
        question_1 = Question.objects.create(indicator=self.indicator, text="This is another question", answer_type="number", order=1)
        questions = self.indicator.questions.order_by('order').all()
        self.assertEqual(questions[0], question_1)
        self.assertEqual(questions[1], question_2)

class QuestionOptionTest(TestCase):
    def setUp(self):
        survey = Survey.objects.create(name='Survey Name', description='Survey description')
        batch = Batch.objects.create(survey=survey)
        indicator = Indicator.objects.create(batch=batch)
        self.question = Question.objects.create(indicator=indicator, text="This is a question", answer_type="multichoice")

    def test_store(self):
        option_2 = QuestionOption.objects.create(question=self.question, text="This is another option", order=2)
        option_1 = QuestionOption.objects.create(question=self.question, text="This is an option", order=1)
        options = self.question.options.order_by('order').all()
        self.assertEqual(len(options), 2)
        options_in_text = "1) %s\n2) %s" % (option_1.text, option_2.text)
        self.assertEqual(self.question.options_in_text(), options_in_text)

class HouseHoldTest(TestCase):
    def test_store(self):
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210")
        household = HouseHold.objects.create(name="HouseHold 1", investigator=investigator)
        self.failUnless(household.id)

class NumericalAnswerTest(TestCase):
    def test_store(self):
        investigator = Investigator.objects.create(name="Investigator", mobile_number="9876543210")
        household = HouseHold.objects.create(name="HouseHold 1", investigator=investigator)
        survey = Survey.objects.create(name='Survey Name', description='Survey description')
        batch = Batch.objects.create(survey=survey)
        indicator = Indicator.objects.create(batch=batch)
        question = Question.objects.create(indicator=indicator, text="This is a question", answer_type="number")

        answer = NumericalAnswer.objects.create(investigator=investigator, household=household, question=question, answer=10)
        self.failUnless(answer.id)