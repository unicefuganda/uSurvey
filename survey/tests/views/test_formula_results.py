from django.test import TestCase
from django.test.client import Client
from rapidsms.contrib.locations.models import Location, LocationType
from survey.models_file import *
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from survey.views.location_widget import LocationWidget

class NumericalFormulaResults(TestCase):
    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_aggregates', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)
        self.client.login(username='Rajni', password='I_Rock')

        self.batch = Batch.objects.create(order=1)
        self.question_1 = Question.objects.create(batch=self.batch, text="Question 1?", answer_type=Question.NUMBER, order=1)
        self.question_2 = Question.objects.create(batch=self.batch, text="Question 2?", answer_type=Question.NUMBER, order=2)

        self.formula_1 = Formula.objects.create(name="Formula 1", numerator=self.question_1, denominator=self.question_2, batch=self.batch)

        district = LocationType.objects.create(name = 'District', slug = 'district')
        village = LocationType.objects.create(name = 'Village', slug = 'village')

        self.kampala = Location.objects.create(name='Kampala', type = district)
        self.village_1 = Location.objects.create(name='Village 1', type = village, tree_parent = self.kampala)
        self.village_2 = Location.objects.create(name='Village 2', type = village, tree_parent = self.kampala)

        backend = Backend.objects.create(name='something')
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=self.village_1, backend = backend, weights = 0.3)
        self.household_1 = Household.objects.create(investigator=investigator)
        self.household_2 = Household.objects.create(investigator=investigator)

        investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", location=self.village_2, backend = backend, weights = 0.9)
        self.household_3 = Household.objects.create(investigator=investigator_1)
        self.household_4 = Household.objects.create(investigator=investigator_1)

        investigator.answered(self.question_1, self.household_1, 20)
        investigator.answered(self.question_2, self.household_1, 200)
        investigator.answered(self.question_1, self.household_2, 10)
        investigator.answered(self.question_2, self.household_2, 100)

        investigator_1.answered(self.question_1, self.household_3, 40)
        investigator_1.answered(self.question_2, self.household_3, 400)
        investigator_1.answered(self.question_1, self.household_4, 50)
        investigator_1.answered(self.question_2, self.household_4, 500)
        for household in Household.objects.all():
            HouseholdHead.objects.create(household=household, surname="Surname %s" % household.pk)


    def test_get(self):
        url = "/batches/%s/formulae/%s/" % (self.batch.pk, self.formula_1.pk)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('formula/show.html', templates)
        self.assertEquals(type(response.context['locations']), LocationWidget)

    def test_get_for_district(self):
        url = "/batches/%s/formulae/%s/?location=%s" % (self.batch.pk, self.formula_1.pk, self.kampala.pk)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('formula/show.html', templates)
        self.assertEquals(type(response.context['locations']), LocationWidget)
        self.assertEquals(response.context['computed_value'], 6)
        self.assertEquals(len(response.context['hierarchial_data']), 2)
        self.assertEquals(response.context['hierarchial_data'][self.village_1], 3)
        self.assertEquals(response.context['hierarchial_data'][self.village_2], 9)

    def test_get_for_village(self):
        url = "/batches/%s/formulae/%s/?location=%s" % (self.batch.pk, self.formula_1.pk, self.village_1.pk)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('formula/show.html', templates)
        self.assertEquals(type(response.context['locations']), LocationWidget)
        self.assertEquals(response.context['computed_value'], 3)
        self.assertEquals(response.context['weights'], 0.3)
        self.assertEquals(len(response.context['household_data']), 2)
        self.assertEquals(response.context['household_data'][self.household_1][self.formula_1.numerator], 20)
        self.assertEquals(response.context['household_data'][self.household_1][self.formula_1.denominator], 200)
        self.assertEquals(response.context['household_data'][self.household_2][self.formula_1.numerator], 10)
        self.assertEquals(response.context['household_data'][self.household_2][self.formula_1.denominator], 100)

class MultichoiceResults(TestCase):
    def setUp(self):
        self.client = Client()
        raj = User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock')
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com', password='I_Suck')
        some_group = Group.objects.create(name='some group')
        auth_content = ContentType.objects.get_for_model(Permission)
        permission, out = Permission.objects.get_or_create(codename='can_view_aggregates', content_type=auth_content)
        some_group.permissions.add(permission)
        some_group.user_set.add(raj)
        self.client.login(username='Rajni', password='I_Rock')

        self.batch = Batch.objects.create(order=1)
        self.question_1 = Question.objects.create(batch=self.batch, text="Question 1?", answer_type=Question.NUMBER, order=1)
        self.question_2 = Question.objects.create(batch=self.batch, text="Question 2?", answer_type=Question.NUMBER, order=2)
        self.question_3 = Question.objects.create(batch=self.batch, text="This is a question", answer_type=Question.MULTICHOICE, order=3)
        self.option_1 = QuestionOption.objects.create(question=self.question_3, text="OPTION 2", order=1)
        self.option_2 = QuestionOption.objects.create(question=self.question_3, text="OPTION 1", order=2)

        self.formula = Formula.objects.create(name="Name", numerator=self.question_3, denominator=self.question_1, batch=self.batch)

        district = LocationType.objects.create(name = 'District', slug = 'district')
        village = LocationType.objects.create(name = 'Village', slug = 'village')

        self.kampala = Location.objects.create(name='Kampala', type = district)
        self.village_1 = Location.objects.create(name='Village 1', type = village, tree_parent = self.kampala)
        self.village_2 = Location.objects.create(name='Village 2', type = village, tree_parent = self.kampala)

        backend = Backend.objects.create(name='something')
        investigator = Investigator.objects.create(name="Investigator 1", mobile_number="1", location=self.village_1, backend = backend, weights = 0.3)
        household_1 = Household.objects.create(investigator=investigator)
        household_2 = Household.objects.create(investigator=investigator)
        household_3 = Household.objects.create(investigator=investigator)
        self.household_1 = household_1
        self.household_2 = household_2
        self.household_3 = household_3

        investigator_1 = Investigator.objects.create(name="Investigator 2", mobile_number="2", location=self.village_2, backend = backend, weights = 0.9)
        household_4 = Household.objects.create(investigator=investigator_1)
        household_5 = Household.objects.create(investigator=investigator_1)
        household_6 = Household.objects.create(investigator=investigator_1)

        investigator.answered(self.question_1, household_1, 20)
        investigator.answered(self.question_3, household_1, 1)
        investigator.answered(self.question_1, household_2, 10)
        investigator.answered(self.question_3, household_2, 1)
        investigator.answered(self.question_1, household_3, 30)
        investigator.answered(self.question_3, household_3, 2)

        investigator_1.answered(self.question_1, household_4, 30)
        investigator_1.answered(self.question_3, household_4, 2)
        investigator_1.answered(self.question_1, household_5, 20)
        investigator_1.answered(self.question_3, household_5, 2)
        investigator_1.answered(self.question_1, household_6, 40)
        investigator_1.answered(self.question_3, household_6, 1)
        for household in Household.objects.all():
            HouseholdHead.objects.create(household=household, surname="Surname %s" % household.pk)


    def test_get_for_district(self):
        url = "/batches/%s/formulae/%s/?location=%s" % (self.batch.pk, self.formula.pk, self.kampala.pk)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('formula/show.html', templates)
        self.assertEquals(type(response.context['locations']), LocationWidget)
        self.assertEquals(response.context['computed_value'], { self.option_1.text: 27.5, self.option_2.text: 32.5})
        self.assertEquals(len(response.context['hierarchial_data']), 2)
        self.assertEquals(response.context['hierarchial_data'][self.village_1], { self.option_1.text: 15, self.option_2.text: 15})
        self.assertEquals(response.context['hierarchial_data'][self.village_2], { self.option_1.text: 40, self.option_2.text: 50})

    def test_get_for_village(self):
        url = "/batches/%s/formulae/%s/?location=%s" % (self.batch.pk, self.formula.pk, self.village_1.pk)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('formula/show.html', templates)
        self.assertEquals(type(response.context['locations']), LocationWidget)
        self.assertEquals(response.context['computed_value'], { self.option_1.text: 15, self.option_2.text: 15})
        self.assertEquals(response.context['weights'], 0.3)
        self.assertEquals(len(response.context['household_data']), 3)
        self.assertEquals(response.context['household_data'][self.household_1][self.formula.numerator], self.option_1)
        self.assertEquals(response.context['household_data'][self.household_1][self.formula.denominator], 20)
        self.assertEquals(response.context['household_data'][self.household_2][self.formula.numerator], self.option_1)
        self.assertEquals(response.context['household_data'][self.household_2][self.formula.denominator], 10)
        self.assertEquals(response.context['household_data'][self.household_3][self.formula.numerator], self.option_2)
        self.assertEquals(response.context['household_data'][self.household_3][self.formula.denominator], 30)
