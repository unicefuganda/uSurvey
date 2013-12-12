from datetime import date
from django.test.client import Client
from django.contrib.auth.models import User
from rapidsms.contrib.locations.models import Location, LocationType
from survey.investigator_configs import PRIME_LOCATION_TYPE
from survey.models import HouseholdMemberGroup, QuestionModule, Investigator, GroupCondition, BatchQuestionOrder
from survey.models.households import HouseholdMember, Household
from survey.models.surveys import Survey
from survey.models.question import Question
from survey.models.batch import Batch
from survey.tests.base_test import BaseTest
from survey.forms.batch import BatchForm, BatchQuestionsForm
import json


class BatchViewsTest(BaseTest):
    def setUp(self):
        self.client = Client()
        user_without_permission = User.objects.create_user(username='useless', email='rajni@kant.com',
                                                           password='I_Suck')
        raj = self.assign_permission_to(User.objects.create_user('Rajni', 'rajni@kant.com', 'I_Rock'),
                                        'can_view_batches')
        raj = self.assign_permission_to(raj, 'can_view_investigators')

        self.client.login(username='Rajni', password='I_Rock')
        self.survey = Survey.objects.create(name='survey name', description='survey descrpition', type=False,
                                            sample_size=10)
        self.batch = Batch.objects.create(order=1, name="Batch A", survey=self.survey)
        country = LocationType.objects.create(name="Country", slug="country")
        self.uganda = Location.objects.create(name="Uganda", type=country)
        district = LocationType.objects.create(name=PRIME_LOCATION_TYPE, slug=PRIME_LOCATION_TYPE)
        self.kampala = Location.objects.create(name="Kampala", type=district, tree_parent=self.uganda)
        city = LocationType.objects.create(name="City", slug="city")
        village = LocationType.objects.create(name="Village", slug="village")
        self.kampala_city = Location.objects.create(name="Kampala City", type=city, tree_parent=self.kampala)
        self.bukoto = Location.objects.create(name="Bukoto", type=city, tree_parent=self.kampala)
        self.kamoja = Location.objects.create(name="kamoja", type=village, tree_parent=self.bukoto)
        self.abim = Location.objects.create(name="Abim", type=district, tree_parent=self.uganda)
        self.batch.open_for_location(self.abim)

    def test_get_index(self):
        response = self.client.get('/surveys/%d/batches/' % self.survey.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/index.html', templates)
        self.assertIn(self.batch, response.context['batches'])
        self.assertEquals(self.survey, response.context['survey'])
        self.assertEquals('/surveys/%d/batches/new/' % self.survey.id, response.context['action'])
        self.assertIsInstance(response.context['batchform'], BatchForm)

    def test_get_index_should_not_show_batches_not_belonging_to_the_survey(self):
        another_batch = Batch.objects.create(order=2, name="Batch B")
        response = self.client.get('/surveys/%d/batches/' % self.survey.id)
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/index.html', templates)
        self.assertIn(self.batch, response.context['batches'])
        self.assertFalse(another_batch in response.context['batches'])
        self.assertEquals(self.survey, response.context['survey'])

    def test_get_batch_view(self):
        self.batch.activate_non_response_for(self.abim)
        response = self.client.get('/surveys/%d/batches/%d/' % (self.survey.id, self.batch.pk))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/show.html', templates)
        self.assertEquals(self.batch, response.context['batch'])
        self.assertIn(self.kampala, response.context['locations'])
        self.assertIn(self.abim, response.context['open_locations'])
        self.assertIn(self.abim, response.context['non_response_active_locations'])

    def test_get_batch_view_with_only_non_response_active_locations_in_context(self):
        self.batch.activate_non_response_for(self.abim)
        self.batch.open_for_location(self.kampala)
        response = self.client.get('/surveys/%d/batches/%d/' % (self.survey.id, self.batch.pk))
        self.assertIn(self.abim, response.context['non_response_active_locations'])
        self.assertNotIn(self.kampala, response.context['non_response_active_locations'])

    def test_open_batch_for_location(self):
        self.assertFalse(self.batch.is_open_for(self.kampala))
        response = self.client.post('/batches/' + str(self.batch.pk) + "/open_to",
                                    data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertTrue(self.batch.is_open_for(loc))
        json_response = json.loads(response.content)
        self.assertEqual('', json_response)

    def test_should_not_activate_non_response_if_batch_is_not_open_for_location(self):
        self.assertFalse(self.batch.is_open_for(self.kampala))
        response = self.client.post('/batches/%s/non_response/activate/' % str(self.batch.pk), data={'non_response_location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)

        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertFalse(self.batch.non_response_is_activated_for(loc))

        json_response = json.loads(response.content)
        self.assertEqual('%s is not open for %s'%(self.batch.name, self.kampala.name), json_response)

    def test_should_activate_non_response_only_if_batch_is_already_open_for_location(self):
        self.batch.open_for_location(self.kampala)
        self.assertFalse(self.batch.non_response_is_activated_for(self.kampala))
        response = self.client.post('/batches/%s/non_response/activate/' % str(self.batch.pk), data={'non_response_location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)

        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertTrue(self.batch.non_response_is_activated_for(loc))

        json_response = json.loads(response.content)
        self.assertEqual('', json_response)

    def test_de_activate_non_response_for_batch_and_location(self):
        self.batch.open_for_location(self.kampala)
        self.batch.activate_non_response_for(self.kampala)
        self.assertTrue(self.batch.non_response_is_activated_for(self.kampala))
        response = self.client.post('/batches/%s/non_response/deactivate/' % str(self.batch.pk), data={'non_response_location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)

        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertFalse(self.batch.non_response_is_activated_for(loc))

        json_response = json.loads(response.content)
        self.assertEqual('', json_response)

    def test_de_activate_non_response_for_batch_only_if_active_location(self):
        self.batch.open_for_location(self.kampala)

        response = self.client.post('/batches/%s/non_response/deactivate/' % str(self.batch.pk), data={'non_response_location_id': self.kampala.pk})
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertFalse(self.batch.non_response_is_activated_for(loc))

        json_response = json.loads(response.content)
        self.assertEqual('', json_response)

    def test_deactivate_non_response_does_nothing_if_not_open(self):
        self.batch.close_for_location(self.kampala)

        response = self.client.post('/batches/%s/non_response/deactivate/' % str(self.batch.pk), data={'non_response_location_id': self.kampala.pk})
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertTrue(self.batch.is_closed_for(loc))
            self.assertFalse(self.batch.non_response_is_activated_for(loc))

        json_response = json.loads(response.content)
        self.assertEqual('', json_response)

    def test_should_not_allow_open_batch_for_location_if_already_open_for_another_survey(self):
        another_survey = Survey.objects.create(name='survey name 2', description='survey descrpition 2', type=False,
                                               sample_size=10)
        another_batch = Batch.objects.create(order=1, name="Batch A", survey=another_survey)
        another_batch.open_for_location(self.kampala)

        self.assertTrue(another_batch.is_open_for(self.kampala))
        self.assertFalse(self.batch.is_open_for(self.kampala))
        response = self.client.post('/batches/' + str(self.batch.pk) + "/open_to",
                                    data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertFalse(self.batch.is_open_for(loc))
        open_batch_error_message = "%s has already open batches from survey %s" % (
            self.kampala.name, another_survey.name)
        json_response = json.loads(response.content)
        self.assertEqual(open_batch_error_message, json_response)

    def test_open_batch_does_not_allow_questions_to_be_assigned(self):
        another_survey = Survey.objects.create(name='survey name 2', description='survey descrpition 2', type=False,
                                               sample_size=10)
        another_batch = Batch.objects.create(order=1, name="Batch A", survey=another_survey)
        another_batch.open_for_location(self.kampala)

        self.assertTrue(another_batch.is_open_for(self.kampala))

        response = self.client.get('/batches/' + str(another_batch.pk) + "/assign_questions/")

        self.assertRedirects(response, "/batches/%s/questions/" % str(another_batch.pk), 302, 200)
        self.assertIn("Questions cannot be assigned to open batch: %s." % another_batch.name.capitalize(),
                      response.cookies['messages'].value)

    def test_close_batch_for_location(self):
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.batch.open_for_location(loc)

        response = self.client.post('/batches/' + str(self.batch.pk) + "/close_to",
                                    data={'location_id': self.kampala.pk})
        self.failUnlessEqual(response.status_code, 200)
        for loc in [self.kampala, self.kampala_city, self.bukoto, self.kamoja]:
            self.assertFalse(self.batch.is_open_for(loc))
        json_response = json.loads(response.content)
        self.assertEqual('', json_response)

    def test_restricted_permssion(self):
        self.assert_restricted_permission_for('/surveys/%d/batches/' % self.survey.id)
        self.assert_restricted_permission_for('/surveys/%d/batches/new/' % self.survey.id)
        self.assert_restricted_permission_for('/surveys/%d/batches/1/' % self.survey.id)
        self.assert_restricted_permission_for('/batches/%d/assign_questions/' % (self.batch.id))
        self.assert_restricted_permission_for('/batches/1/open_to')
        self.assert_restricted_permission_for('/batches/1/close_to')
        self.assert_restricted_permission_for('/surveys/%d/batches/%d/edit/' % (self.survey.id, self.batch.id))
        self.assert_restricted_permission_for('/surveys/%d/batches/%d/delete/' % (self.survey.id, self.batch.id))
        self.assert_login_required('/surveys/%d/batches/check_name/' % (self.survey.id))


    def test_add_new_batch_should_load_new_template(self):
        response = self.client.get('/surveys/%d/batches/new/' % self.survey.id)
        self.assertEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/new.html', templates)

    def test_batch_form_is_in_response_request_context(self):
        response = self.client.get('/surveys/%d/batches/new/' % self.survey.id)
        self.assertIsInstance(response.context['batchform'], BatchForm)
        self.assertEqual(response.context['button_label'], 'Create')
        self.assertEqual(response.context['id'], 'add-batch-form')
        self.assertEqual(response.context['action'], '/surveys/%d/batches/new/' % self.survey.id)
        self.assertEqual(response.context['title'], 'New Batch')
        self.assertEqual(response.context['cancel_url'], '/surveys/')

    def test_post_add_new_batch_is_invalid_if_name_field_is_empty(self):
        response = self.client.post('/surveys/%d/batches/new/' % self.survey.id, data={'name': '', 'description': ''})
        self.assertTrue(len(response.context['batchform'].errors) > 0)

    def test_post_add_new_batch(self):
        data = {'name': 'Batch1', 'description': 'description'}
        response = self.client.post('/surveys/%d/batches/new/' % self.survey.id, data=data)
        self.assertEqual(len(Batch.objects.filter(survey__id=self.survey.id, **data)), 1)

    def test_post_add_new_batch_redirects_to_batches_table_if_valid(self):
        response = self.client.post('/surveys/%d/batches/new/' % self.survey.id,
                                    data={'name': 'Batch1', 'description': 'description'})
        self.assertRedirects(response, expected_url='/surveys/%d/batches/' % self.survey.id, status_code=302,
                             target_status_code=200, msg_prefix='')

    def test_post_add_new_batch_should_add_batch_to_the_survey(self):
        form_data = {'name': 'Some Batch', 'description': 'some description'}
        self.failIf(Batch.objects.filter(**form_data))
        response = self.client.post('/surveys/%d/batches/new/' % self.survey.id, data=form_data)
        batch = Batch.objects.get(**form_data)
        self.assertEqual(self.survey, batch.survey)

    def test_edit_batch_should_load_new_template(self):
        batch = Batch.objects.create(survey=self.survey, name="batch a", description="batch a description")
        response = self.client.get('/surveys/%d/batches/%d/edit/' % (self.survey.id, self.batch.id))
        self.assertEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/new.html', templates)

    def test_edit_batch_page_gets_batch_form_instance(self):
        batch = Batch.objects.create(survey=self.survey, name="batch a", description="batch a description")
        response = self.client.get('/surveys/%d/batches/%d/edit/' % (self.survey.id, batch.id))
        self.assertIsInstance(response.context['batchform'], BatchForm)
        self.assertEqual(response.context['batchform'].initial['name'], batch.name)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEqual(response.context['action'], '/surveys/%d/batches/%d/edit/' % (self.survey.id, batch.id))
        self.assertEqual(response.context['id'], 'edit-batch-form')

    def test_save_edited_batch(self):
        batch = Batch.objects.create(survey=self.survey, name="batch a", description="batch a description")
        form_data = {
            'name': 'batch aaa',
            'description': batch.description
        }
        response = self.client.post('/surveys/%d/batches/%d/edit/' % (self.survey.id, batch.id), data=form_data)
        updated_batch = Batch.objects.get(name=form_data['name'])
        self.failUnless(updated_batch)
        self.failIf(Batch.objects.filter(id=batch.id, name=batch.name))
        self.assertRedirects(response, expected_url='/surveys/%d/batches/' % self.survey.id, status_code=302,
                             target_status_code=200, msg_prefix='')

    def test_delete_batch(self):
        self.batch.close_for_location(self.abim)
        self.assertFalse(self.batch.is_open())
        response = self.client.get('/surveys/%d/batches/%d/delete/' % (self.survey.id, self.batch.id))
        recovered_batch = Batch.objects.filter(id=self.batch.id)
        self.assertRedirects(response, expected_url='/surveys/%d/batches/' % self.survey.id, status_code=302,
                             target_status_code=200, msg_prefix='')
        self.failIf(recovered_batch)

    def test_should_not_delete_batch_if_open(self):
        self.batch.open_for_location(self.kampala)
        response = self.client.get('/surveys/%d/batches/%d/delete/' % (self.survey.id, self.batch.id))
        recovered_batch = Batch.objects.filter(id=self.batch.id)
        self.assertRedirects(response, expected_url='/surveys/%d/batches/' % self.survey.id, status_code=302,
                             target_status_code=200, msg_prefix='')
        self.assertIn("Batch cannot be deleted because it is open in Kampala District, Abim District.", response.cookies['messages'].value)
        self.failUnless(recovered_batch)

    def test_should_not_delete_batch_if_batches_questions_have_been_responded_to(self):
        investigator = Investigator.objects.create(mobile_number="123456789", name="Rajni", location=self.kampala)
        household = Household.objects.create(investigator=investigator, location=investigator.location)
        member = HouseholdMember.objects.create(surname="haha", date_of_birth=date(1990, 02, 01), household=household)
        group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        female = GroupCondition.objects.create(attribute="gender", value=True, condition="EQUALS")
        group.conditions.add(female)
        module = QuestionModule.objects.create(name="Education")
        question_1 = Question.objects.create(group=group, text="Haha?", module=module, answer_type=Question.NUMBER,
                                             order=1)
        question_2 = Question.objects.create(group=group, text="Haha?", module=module, answer_type=Question.NUMBER,
                                             order=2)
        question_3 = Question.objects.create(group=group, text="Haha?", module=module, answer_type=Question.NUMBER,
                                             order=3)

        question_1.batches.add(self.batch)
        question_2.batches.add(self.batch)
        question_3.batches.add(self.batch)

        BatchQuestionOrder.objects.create(batch=self.batch, question=question_1, order=1)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_2, order=2)
        BatchQuestionOrder.objects.create(batch=self.batch, question=question_3, order=3)

        self.batch.open_for_location(self.kampala)
        investigator.member_answered(question_1, member, 1, self.batch)
        investigator.member_answered(question_2, member, 1, self.batch)
        investigator.member_answered(question_3, member, 1, self.batch)
        self.batch.close_for_location(self.kampala)
        response = self.client.get('/surveys/%d/batches/%d/delete/' % (self.survey.id, self.batch.id))
        recovered_batch = Batch.objects.filter(id=self.batch.id)
        self.assertRedirects(response, expected_url='/surveys/%d/batches/' % self.survey.id, status_code=302,
                             target_status_code=200, msg_prefix='')
        self.assertIn("Batch cannot be deleted because it has responses.", response.cookies['messages'].value)
        self.failUnless(recovered_batch)

    def test_assign_question_to_the_batch_should_show_list_of_questions(self):
        group = HouseholdMemberGroup.objects.create(name="Females", order=1)
        module_1 = QuestionModule.objects.create(name="Education")
        module_2 = QuestionModule.objects.create(name="Health")
        question_1 = Question.objects.create(group=group, text="Haha?", module=module_1)
        question_2 = Question.objects.create(group=group, text="Haha?", module=module_1)
        question_3 = Question.objects.create(group=group, text="Haha?", module=module_2)

        self.batch.close_for_location(self.abim)

        response = self.client.get('/batches/%d/assign_questions/' % (self.batch.id))
        self.failUnlessEqual(response.status_code, 200)
        templates = [template.name for template in response.templates]
        self.assertIn('batches/assign.html', templates)
        self.assertEqual(3, len(response.context['batch_questions_form'].fields['questions']._queryset))
        self.assertIn(question_1, response.context['batch_questions_form'].fields['questions']._queryset)
        self.assertIn(question_2, response.context['batch_questions_form'].fields['questions']._queryset)
        self.assertIn(question_3, response.context['batch_questions_form'].fields['questions']._queryset)
        self.assertEqual(self.batch, response.context['batch'])
        self.assertIsInstance(response.context['batch_questions_form'], BatchQuestionsForm)
        self.assertEqual(response.context['button_label'], 'Save')
        self.assertEqual(response.context['id'], 'assign-question-to-batch-form')
        self.assertEqual(1, len(response.context['groups']))
        self.assertIn(group, response.context['groups'])
        [self.assertIn(module, response.context['modules']) for module in [module_1, module_2]]

    def test_post_assign_questions_to_batch_should_save_questions(self):
        q1 = Question.objects.create(text="question1", answer_type=Question.NUMBER)
        q2 = Question.objects.create(text="question2", answer_type=Question.TEXT)
        form_data = {
            'questions': [q1.id, q2.id],
        }
        self.batch.close_for_location(self.abim)

        self.failIf(self.batch.all_questions())
        response = self.client.post('/batches/%d/assign_questions/' % (self.batch.id), data=form_data)
        self.assertRedirects(response, expected_url='batches/%d/questions/' % self.batch.id, status_code=302,
                             target_status_code=200, msg_prefix='')
        self.assertEqual(2, len(self.batch.all_questions()))
        self.assertIn(q1, self.batch.all_questions())
        self.assertIn(q2, self.batch.all_questions())
        success_message = "Questions successfully assigned to batch: %s." % self.batch.name.capitalize()
        self.assertTrue(success_message in response.cookies['messages'].value)

    def test_should_tell_if_name_is_already_taken(self):
        batch = Batch.objects.create(survey=self.survey, name="batch a", description="batch a description")
        response = self.client.get('/surveys/%d/batches/check_name/?name=%s' % (self.survey.id, batch.name))
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response)

        response = self.client.get(
            '/surveys/%d/batches/check_name/?name=%s' % (self.survey.id, 'some other name that does not exist'))
        self.failUnlessEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response)

    def test_list_questions_under_batch_should_bring_only_questions_and_not_subquestion(self):
        batch = Batch.objects.create(survey=self.survey, name="batch a", description="batch a description")
        q1 = Question.objects.create(text="question1", answer_type=Question.NUMBER)
        q2 = Question.objects.create(text="question2", answer_type=Question.TEXT)
        q1.batches.add(batch)
        q2.batches.add(batch)

        BatchQuestionOrder.objects.create(batch=batch, question=q1, order=1)
        BatchQuestionOrder.objects.create(batch=batch, question=q2, order=2)

        sub_question1 = Question.objects.create(text='sub1', answer_type=Question.NUMBER, subquestion=True, parent=q1)
        sub_question2 = Question.objects.create(text='sub2', answer_type=Question.NUMBER, subquestion=True, parent=q1)
        sub_question3 = Question.objects.create(text='sub3', answer_type=Question.NUMBER, subquestion=True, parent=q2)
        sub_question1.batches.add(batch)
        sub_question2.batches.add(batch)
        sub_question3.batches.add(batch)

        BatchQuestionOrder.objects.create(batch=batch, question=sub_question1, order=1)
        BatchQuestionOrder.objects.create(batch=batch, question=sub_question2, order=2)
        BatchQuestionOrder.objects.create(batch=batch, question=sub_question3, order=3)

        response = self.client.get('/batches/%s/questions/' % batch.id)
        self.assertIn(q1, response.context['questions'])
        self.assertIn(q2, response.context['questions'])
        self.assertNotIn(sub_question1, response.context['questions'])

    def test_updates_batch_orders_when_are_edited(self):
        batch = Batch.objects.create(survey=self.survey, name="batch a", description="batch a description")
        q1 = Question.objects.create(text="question1", answer_type=Question.NUMBER)
        q2 = Question.objects.create(text="question2", answer_type=Question.TEXT)
        q1.batches.add(batch)
        q2.batches.add(batch)

        BatchQuestionOrder.objects.create(batch=batch, question=q1, order=1)
        BatchQuestionOrder.objects.create(batch=batch, question=q2, order=2)
        order_one = 1
        order_two = 2
        order_update_form_data = {'order_information': ['%s-%s' % (order_two, q1.id), '%s-%s' % (order_one, q2.id)]}

        response = self.client.post('/batches/%s/update_question_orders/' % batch.id, data=order_update_form_data)

        question_order_1 = BatchQuestionOrder.objects.get(order=order_one)
        question_order_2 = BatchQuestionOrder.objects.get(order=order_two)

        self.assertEqual(question_order_1.question, q2)
        self.assertEqual(question_order_2.question, q1)

        self.assertRedirects(response, "/batches/%s/questions/" % batch.id, status_code=302, target_status_code=200)
        message = "Question orders successfully updated for batch: %s." % batch.name.capitalize()
        self.assertIn(message, response.cookies['messages'].value)

    def test_updates_batch_orders_when_are_edited_even_if_batch_question_object_does_not_exist(self):
        batch = Batch.objects.create(survey=self.survey, name="batch a", description="batch a description")
        q1 = Question.objects.create(text="question1", answer_type=Question.NUMBER)
        q2 = Question.objects.create(text="question2", answer_type=Question.TEXT)
        q1.batches.add(batch)
        q2.batches.add(batch)

        order_one = 1
        order_two = 2
        order_update_form_data = {'order_information': ['%s-%s' % (order_two, q1.id), '%s-%s' % (order_one, q2.id)]}

        response = self.client.post('/batches/%s/update_question_orders/' % batch.id, data=order_update_form_data)

        question_order_1 = BatchQuestionOrder.objects.get(order=order_one)
        question_order_2 = BatchQuestionOrder.objects.get(order=order_two)

        self.assertEqual(question_order_1.question, q2)
        self.assertEqual(question_order_2.question, q1)

        self.assertRedirects(response, "/batches/%s/questions/" % batch.id, status_code=302, target_status_code=200)
        message = "Question orders successfully updated for batch: %s." % batch.name.capitalize()
        self.assertIn(message, response.cookies['messages'].value)

    def test_sends_error_message_if_no_new_orders_are_posted(self):
        batch = Batch.objects.create(survey=self.survey, name="batch a", description="batch a description")
        q1 = Question.objects.create(text="question1", answer_type=Question.NUMBER)
        q2 = Question.objects.create(text="question2", answer_type=Question.TEXT)
        q1.batches.add(batch)
        q2.batches.add(batch)

        BatchQuestionOrder.objects.create(batch=batch, question=q1, order=1)
        BatchQuestionOrder.objects.create(batch=batch, question=q2, order=2)

        order_update_form_data = {'order_information': []}

        response = self.client.post('/batches/%s/update_question_orders/' % batch.id, data=order_update_form_data)
        self.assertRedirects(response, "/batches/%s/questions/" % batch.id, status_code=302, target_status_code=200)
        error_message = "No questions orders were updated."
        self.assertIn(error_message, response.cookies['messages'].value)

    def test_ajax_request_batch_list_under_a_survey(self):
        survey_1 = Survey.objects.create(name="survey A")
        survey_2 = Survey.objects.create(name="survey B")
        batch_1 = Batch.objects.create(name="batch1", order=1, survey=survey_1)
        batch_2 = Batch.objects.create(name="batch2", order=2, survey=survey_1)
        response = self.client.get('/surveys/%s/batches/' % survey_1.id, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        content = json.loads(response.content)
        self.assertEquals(len(content), 2)

        self.assertEqual(batch_1.id, content[0]['id'])
        self.assertEqual(batch_1.name, content[0]['name'])
        self.assertEqual(batch_2.id, content[1]['id'])
        self.assertEqual(batch_2.name, content[1]['name'])

    def test_ajax_request_batch_list_all(self):
        Batch.objects.all().delete()
        batch_1 = Batch.objects.create(name="batch1", order=1)
        batch_2 = Batch.objects.create(name="batch2", order=2)
        response = self.client.get('/batches/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        content = json.loads(response.content)
        self.assertEquals(len(content), 2)

        self.assertEqual(batch_1.id, content[0]['id'])
        self.assertEqual(batch_1.name, content[0]['name'])
        self.assertEqual(batch_2.id, content[1]['id'])
        self.assertEqual(batch_2.name, content[1]['name'])

    def test_batch_list_all_shows_nothing(self):
        response = self.client.get('/batches/')
        self.assertEqual(200, response.status_code)
        templates = [template.name for template in response.templates]
        self.assertIn('layout.html', templates)
