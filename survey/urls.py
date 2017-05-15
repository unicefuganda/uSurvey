import os
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.views.generic import TemplateView
from survey.models import ListingTemplate, Batch,\
    ParameterTemplate, QuestionTemplate
from survey.forms.password_mgt import uSurveyPasswordResetForm

from django.views.static import serve as staticserve

urlpatterns = patterns(
    '',
    (r'^static/(?P<path>.*)$', staticserve,
        {'document_root': os.path.join(os.path.dirname(__file__), 'static')}),
    url(r'^$', 'survey.views.home_page.index', name='main_page'),
    url(r'^home/$', 'survey.views.home_page.home', name='home_page'),
    url(r'^about/$', 'survey.views.home_page.about', name='about_page'),
    url(
        r'^about/edit/$',
        'survey.views.home_page.edit',
        name='edit_about_page'),
    url(
        r'^discover/$',
        TemplateView.as_view(
            template_name="main/discover.html"),
        name='discover'),
    url(
        r'^contact/$',
        TemplateView.as_view(
            template_name="main/contact.html"),
        name='contact'),
    url(
        r'^success-story/$',
        'survey.views.home_page.home_success_story_list',
        name='home_success_story_list'),
    url(
        r'^success-stories/$',
        'survey.views.home_page.success_story_list',
        name='success_story_list'),
    url(
        r'^success-story/new/$',
        'survey.views.home_page.success_story_form',
        name='success_story_new'),
    url(
        r'^success-story/(?P<id>\d+)/$',
        'survey.views.home_page.success_story_form',
        name='success_story_edit'),
    url(
        r'^success-story/delete/(?P<id>\d+)/$',
        'survey.views.home_page.success_story_delete',
        name='success_story_delete'),
    # """
    # url(
    #     r'^locations/hierarchy/add/$',
    #     'survey.views.location_hierarchy.add',
    #     name='add_location_hierarchy'),
    # url(
    #     r'^locations/upload/$',
    #     'survey.views.location_hierarchy.upload',
    #     name='upload_locations'),
    # """
    url(
        r'^locations/weights/upload/$',
        'survey.views.location_weights.upload',
        name='upload_weights'),
    url(
        r'^locations/weights/$',
        'survey.views.location_weights.list_weights',
        name='list_weights_page'),
    url(
        r'^locations/weights/error_logs/$',
        'survey.views.location_weights.error_logs',
        name='weights_error_logs_page'),
    url(
        r'^locations/(?P<location_id>\d+)/children',
        'survey.views.locations.children',
        name='get_location_children'),
    url(
        r'^locations/(?P<location_id>\d+)/enumeration_areas',
        'survey.views.locations.enumeration_areas',
        name='get_enumeration_areas'),
    url(
        r'^interviewers/$',
        'survey.views.interviewer.list_interviewers',
        name="interviewers_page"),
    url(
        r'^interviewers/export/$',
        'survey.views.interviewer.download_interviewers',
        name="download_interviewers"),
    url(
        r'^interviewers/completion_summary/(?P<interviewer_id>\d+)/$',
        'survey.views.interviewer.show_completion_summary',
        name="interviewer_completion_summary"),
    url(
        r'^interviewers/new/$',
        'survey.views.interviewer.new_interviewer',
        name="new_interviewer_page"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/$',
        'survey.views.interviewer.show_interviewer',
        name="show_interviewer_page"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/block/$',
        'survey.views.interviewer.block_interviewer',
        name="block_interviewer_page"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/block_odk/$',
        'survey.views.interviewer.block_odk',
        name="block_interviewer_odk"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/block_ussd/$',
        'survey.views.interviewer.block_ussd',
        name="block_interviewer_ussd"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/unblock_odk/$',
        'survey.views.interviewer.unblock_odk',
        name="unblock_interviewer_odk"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/unblock_ussd/$',
        'survey.views.interviewer.unblock_ussd',
        name="unblock_interviewer_ussd"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/unblock/$',
        'survey.views.interviewer.unblock_interviewer',
        name="unblock_interviewer_page"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/(?P<mode>\w+)/$',
        'survey.views.interviewer.edit_interviewer',
        name="view_interviewer_page"),
    url(
        r'^interviewers/(?P<interviewer_id>\d+)/edit/$',
        'survey.views.interviewer.edit_interviewer',
        name="edit_interviewer_page"),
    url(
        r'^interviewers/check_mobile_number',
        'survey.views.interviewer.check_mobile_number',
        name="check_mobile_number"),
    url(
        r'^ussd/simulator',
        permission_required(
            'auth.can_view_interviewers')(TemplateView.as_view(
            template_name="ussd/simulator.html")),
        name='simulator_page'),
    url(
        r'^online/simulator/(?P<qset_id>\d+)/$',
        'survey.online.simulator.handle_request',
        name="test_qset_flow"),
    url(
        r'^online/restart/(?P<access_id>\d+)/$',
        'survey.online.online_handler.restart',
        name="refresh_data_entry"),
    url(
        r'^online/interviewer/participation/$',
        'survey.online.views.respond',
        name="online_interviewer_view"),
    url(
        r'^ussd',
        'survey.online.views.ussd_flow',
        name="ussd"),
    url(
        r'^aggregates/spreadsheet_report/$',
        'survey.views.excel.download',
        name='excel_report'),
    url(
        r'^aggregates/spreadsheet_results/(?P<batch_id>\d+)/$',
        'survey.views.excel.download_results',
        name='download_export_results'),
    url(
        r'^aggregates/download_spreadsheet',
        'survey.views.excel.download',
        name='download_excel'),
    url(
        r'^interviewer_report/',
        'survey.views.excel.interviewer_report',
        name='interviewer_report_page'),
    url(
        r'^interviewers/completed/download/',
        'survey.views.excel.completed_interviewer',
        name='download_interviewer_excel'),
    url(
        r'^accounts/login/$',
        'django.contrib.auth.views.login',
        {'template_name': 'accounts/login.html'},
        name='login_page'),
    url(
        r'^user/password/reset/$',
        'django.contrib.auth.views.password_reset',
        {'post_reset_redirect': '/user/password/reset/done/', 'password_reset_form': uSurveyPasswordResetForm},
        name="password_reset"),
    url(
        r'^user/password/reset/done/$',
        'django.contrib.auth.views.password_reset_done'),
    url(
        r'^user/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'post_reset_redirect': '/user/password/done/', },
        name='password_reset_url'),
    url(
        r'^user/password/done/$',
        'django.contrib.auth.views.password_reset_complete'),
    url(
        r'^accounts/logout/$',
        'django.contrib.auth.views.logout_then_login',
        name='logout_page'),
    url(
        r'^accounts/reset_password/$',
        'django.contrib.auth.views.password_change',
        {
            'template_name': 'accounts/reset_password.html',
            'post_change_redirect': '/accounts/reset_password/done/',
            'password_change_form': PasswordChangeForm},
        name='password_change'),
    url(
        r'^accounts/reset_password/done/$',
        TemplateView.as_view(
            template_name='accounts/password_reset_done.html'),
        name='password_reset_done'),
    url(
        r'^bulk_sms$',
        'survey.views.bulk_sms.view',
        name='bulk_sms'),
    url(
        r'^bulk_sms/send$',
        'survey.views.bulk_sms.send',
        name='send_bulk_sms'),
    url(
        r'^users/$',
        'survey.views.users.index',
        name='users_index'),
    url(
        r'^users/new/$',
        'survey.views.users.new',
        name='new_user_page'),
    url(
        r'^users/(?P<user_id>\d+)/deactivate/$',
        'survey.views.users.deactivate',
        name='deactivate_user'),
    url(
        r'^users/(?P<user_id>\d+)/activate/$',
        'survey.views.users.activate',
        name='activate_user'),
    url(
        r'^users/(?P<user_id>\d+)/(?P<mode>\w+)/$',
        'survey.views.users.edit',
        name='users_edit'),
    url(
        r'^users/(?P<user_id>\d+)/$',
        'survey.views.users.edit',
        name='users_edit_profile'),
    url(
        r'^users/(?P<user_id>\d+)/$',
        'survey.views.users.show',
        name='users_show_details'),
    url(
        r'^users/download/$',
        'survey.views.users.download_users',
        name='download_users'),
    url(
        r'^users/(?P<user_id>\d+)/(?P<mode>\w+)/$',
        'survey.views.users.edit',
        name='users_edit'),
    url(
        r'^users/(?P<user_id>\d+)/$',
        'survey.views.users.edit',
        name='users_edit_profile'),
    # """
    # url(r'^batches/(?P<batch_id>\d+)/assign_questions/$',
    # 'survey.views.batch./completion/json/', name='assign_questions_page'),
    # """
    url(
        r'^qset/(?P<qset_id>\d+)/assign_questions/$',
        'survey.views.set_questions.assign',
        name='qset_assign_questions_page'),
    url(
        r'^qset/(?P<qset_id>\d+)/update_question_orders/$',
        'survey.views.set_questions.update_orders',
        name='qset_update_question_order_page'),
    url(
        r'^batches/(?P<batch_id>\d+)/update_question_orders/$',
        'survey.views.batch.update_orders',
        name='update_question_order_page'),
    url(
        r'^batches/(?P<batch_id>\d+)/questions/$',
        'survey.views.questions.index',
        name='batch_questions_page'),
    url(
        r'^qsets/(?P<qset_id>\d+)/questions/$',
        'survey.views.set_questions.index',
        name='qset_questions_page'),
    url(
        r'^batches/(?P<batch_id>\d+)/submit_questions/$',
        'survey.views.questions.submit',
        name='batch_questions_submission'),
    url(
        r'^batches/(?P<batch_id>\d+)/questions/export/$',
        'survey.views.questions.export_batch_questions',
        name='export_questions_in_batch'),
    url(
        r'^qset/(?P<qset_id>\d+)/questions/export/$',
        'survey.views.set_questions.export_batch_questions',
        name='export_questions_in_qset'),
    url(
        r'^batches/(?P<batch_id>\d+)/open_to$',
        'survey.views.batch.open',
        name='batch_open_page'),
    url(
        r'^batches/(?P<batch_id>\d+)/all_locs$',
        'survey.views.batch.all_locs',
        name='batch_all_locs'),
    url(
        r'^batches/(?P<batch_id>\d+)/non_response/activate/$',
        'survey.views.batch.activate_non_response',
        name="activate_non_response_page"),
    url(
        r'^batches/(?P<batch_id>\d+)/non_response/deactivate/$',
        'survey.views.batch.deactivate_non_response',
        name="deactivate_non_response_page"),
    url(
        r'^batches/(?P<batch_id>\d+)/close_to$',
        'survey.views.batch.close',
        name='batch_close_page'),
    url(
        r'^batches/(?P<batch_id>\d+)/questions/(?P<question_id>\d+)/add_logic/$',
        'survey.views.questions.add_logic',
        name='add_question_logic_page'),
    url(
        r'^qsets/(?P<qset_id>\d+)/questions/(?P<question_id>\d+)/add_logic/$',
        'survey.views.set_questions.add_logic',
        name='add_qset_question_logic_page'),
    url(
        r'^batches/questions/delete_logic/(?P<flow_id>\d+)/$',
        'survey.views.questions.delete_logic',
        name='delete_question_logic_page'),
    url(
        r'^qset/questions/delete_logic/(?P<flow_id>\d+)/$',
        'survey.views.set_questions.delete_logic',
        name='delete_qset_question_logic_page'),
    url(
        r'^batches/(?P<batch_id>\d+)/questions/(?P<question_id>\d+)/questions_json/$',
        'survey.views.questions.get_questions_for_batch',
        name='batch_questions_json_page'),
    url(
        r'^batches/(?P<batch_id>\d+)/questions/sub_questions/new/$',
        'survey.views.questions.new_subquestion',
        name='add_batch_subquestion_page'),
    url(
        r'^qset/batches/(?P<batch_id>\d+)/questions/sub_questions/new/$',
        'survey.views.set_questions.new_subquestion',
        name='add_qset_subquestion_page'),
    url(
        r'^batches/(?P<batch_id>\d+)/questions/(?P<question_id>\d+)/sub_questions/edit/$',
        'survey.views.questions.edit_subquestion',
        name='edit_batch_subquestion_page'),
    # """
    # url(
    # r'^batches/(?P<batch_id>\d+)/questions/(?P<question_id>\d+)/delete/$',
    # 'survey.views.questions.delete', name='delete_batch_question_page'),
    # """
    url(
        r'^batches/(?P<batch_id>\d+)/questions/(?P<question_id>\d+)/remove/$',
        'survey.views.questions.remove',
        name='remove_question_page'),

    url(
        r'^qset/batches/questions/(?P<question_id>\d+)/remove/$',
        'survey.views.set_questions.remove',
        name='remove_qset_question_page'),

    url(
        r'^qset/batches/questions/(?P<loop_id>\d+)/remove_loop/$',
        'survey.views.set_questions.remove_loop',
        name='remove_question_loop_page'),
    url(
        r'^batches/$',
        'survey.views.batch.list_batches'),
    url(
        r'^qsets/$',
        'survey.views.question_set.list_qsets',
        name='view_qsets'),
    url(
        r'^list_questions/$',
        'survey.views.question_set.list_questions',
        name='list_questions'),
    url(
        r'^question_validators/$',
        'survey.views.question_set.question_validators',
        name='question_validators'),
    url(r'^question_options/$',
        'survey.views.question_set.question_options',
        name='question_options'),
    url(
        r'^batches/list_all_questions/$',
        'survey.views.batch.list_all_questions',
        name='list_all_questions'),
    url(
        r'^batches/list_batch_questions/$',
        'survey.views.batch.list_batch_questions',
        name='list_batch_questions'),
    url(
        r'^qset/qset_identifiers/$',
        'survey.views.question_set.identifiers',
        name='qset_identifiers'),
    url(
        r'^groups/$',
        'survey.views.respondent_group.index',
        name='respondent_groups_page'),
    url(
        r'^groups/new/$',
        'survey.views.respondent_group.add_group',
        name='new_respondent_groups_page'),
    url(
        r'^groups/(?P<group_id>\d+)/edit/$',
        'survey.views.respondent_group.edit_group',
        name='respondent_groups_edit'),
    url(
        r'^groups/(?P<group_id>\d+)/delete/$',
        'survey.views.respondent_group.delete_group',
        name='respondent_groups_delete'),
    # """
    # url(
    #     r'^conditions/$',
    #     'survey.views.respondent_group.conditions',
    #     name='show_group_condition'),
    # url(
    #     r'^conditions/new/$',
    #     'survey.views.respondent_group.add_condition',
    #     name='new_group_condition'),
    # """
    url(
        r'^conditions/(?P<condition_id>\d+)/delete/$',
        'survey.views.respondent_group.delete_condition',
        name='delete_condition_page'),
    url(
        r'^surveys/$',
        'survey.views.surveys.index',
        name='survey_list_page'),
    url(
        r'^surveys/wipe_data/(?P<survey_id>\d+)$',
        'survey.views.surveys.wipe_survey_data',
        name='wipe_survey_data'),
    # """
    # url(
    #     r'^surveys/(?P<survey_id>\d+)/manage$',
    #     'survey.views.surveys.manage',
    #     name='manage_survey_page'),
    # """
    url(
        r'^surveys/new/$',
        'survey.views.surveys.new',
        name='new_survey_page'),
    url(
        r'^surveys/(?P<survey_id>\d+)/edit/$',
        'survey.views.surveys.edit',
        name='edit_survey_page'),
    url(
        r'^surveys/(?P<survey_id>\d+)/clone/$',
        'survey.views.surveys.clone_survey',
        name='clone_survey_page'),
    url(
        r'^listing_form/(?P<qset_id>\d+)/clone/$',
        'survey.views.question_set.clone_qset',
        name='clone_qset_page'),
    url(
        r'^qset/(?P<qset_id>\d+)/clone/$',
        'survey.views.question_set.clone_qset',
        name='clone_qset_page'),
    url(
        r'^surveys/(?P<survey_id>\d+)/delete/$',
        'survey.views.surveys.delete',
        name='delete_survey'),
    url(
        r'^surveys/(?P<survey_id>\d+)/batches/$',
        'survey.views.batch.index',
        name='batch_index_page'),
    url(
        r'^surveys/(?P<survey_id>\d+)/survey_batches/$',
        'survey.views.batch.batches',
        name='survey_batches_page'),
    url(
        r'^surveys/(?P<survey_id>\d+)/batches/new/$',
        'survey.views.batch.new',
        name='new_batch_page'),
    url(
        r'^surveys/(?P<survey_id>\d+)/batches/(?P<batch_id>\d+)/$',
        'survey.views.batch.show',
        name='batch_show_page'),
    url(
        r'^surveys/batches/$',
        'survey.views.batch.index',
        name='%s_home' % Batch.resolve_tag()),
    url(
        r'^surveys/batches/(?P<batch_id>\d+)/edit/$',
        'survey.views.batch.edit',
        name='edit_%s_page' % Batch.resolve_tag()),
    url(
        r'^surveys/interviewers_completion/$',
        'survey.views.survey_completion.show_interviewer_completion_summary',
        name='show_interviewer_completion_summary'),
    url(
        r'^survey/(?P<survey_id>\d+)/completion/json/$',
        'survey.views.survey_completion.completion_json',
        name='survey_completion_json'),
    url(
        r'^survey/completion/json/$',
        'survey.views.survey_completion.json_summary',
        name='survey_json_summary'),
    url(
        r'^survey/survey_indicators/json/$',
        'survey.views.survey_completion.indicators_json',
        name='survey_indicators'),
    url(
        r'^survey/survey_parameters/json/$',
        'survey.views.survey_completion.survey_parameters',
        name='survey_parameters'),
    url(
        r'^surveys/(?P<survey_id>\d+)/batches/(?P<batch_id>\d+)/delete/$',
        'survey.views.batch.delete',
        name='delete_batch'),
    url(
        r'^activate_super_powers_page/$',
        'survey.views.home_page.activate_super_powers',
        name='activate_super_powers_page'),
    url(
        r'^deactivate_super_powers_page/$',
        'survey.views.home_page.deactivate_super_powers',
        name='deactivate_super_powers_page'),
    url(
        r'^surveys/(?P<survey_id>\d+)/sampling_criteria/$',
        'survey.views.surveys.sampling_criteria',
        name='listing_criteria_page'),
    url(
        r'^surveys/(?P<criterion_id>\d+)/delete_sampling_criterion/$',
        'survey.views.surveys.delete_sampling_criterion',
        name='delete_listing_criterion'),
    url(
        r'^surveys/(?P<survey_id>\d+)/batches/check_name/$',
        'survey.views.batch.check_name'),
    url(
        r'^question_library/$',
        'survey.views.question_template.index',
        name='show_%s' % QuestionTemplate.resolve_tag()),
    url(
        r'^question_library/new/$',
        'survey.views.question_template.add',
        name='new_%s' % QuestionTemplate.resolve_tag()),
    url(
        r'^question_library/(?P<question_id>\d+)/edit/$',
        'survey.views.question_template.edit',
        name='edit_%s' % QuestionTemplate.resolve_tag()),
    url(
        r'^question_library/(?P<question_id>\d+)/delete/$',
        'survey.views.question_template.delete',
        name='delete_question_template_page'),
    url(
        r'^question_library/export/$',
        'survey.views.question_template.export_questions',
        name='export_%s' % QuestionTemplate.resolve_tag()),
    url(
        r'^parameter_template/$',
        'survey.views.question_template.index',
        {'model_class': ParameterTemplate},
        name='show_%s' % ParameterTemplate.resolve_tag()),
    url(
        r'^parameter_template/new/$',
        'survey.views.question_template.add',
        {'model_class': ParameterTemplate},
        name='new_%s' % ParameterTemplate.resolve_tag()),
    url(
        r'^question_library/(?P<question_id>\d+)/edit/$',
        'survey.views.question_template.edit',
        name='edit_%s' % ParameterTemplate.resolve_tag()),
    url(
        r'^parameter_template/export/$',
        'survey.views.question_template.export_questions',
        {'model_class': ParameterTemplate},
        name='export_%s' % ParameterTemplate.resolve_tag()),
    url(
        r'^question_library/json_filter/',
        'survey.views.question_template.filter',
        name='filter_question_list'),
    # """
    # url(r'^questions/new/$', 'survey.views.questions.new', name='new_question_page'),
    # url(r'^questions/(?P<question_id>\d+)/is_multichoice/$', 'survey.views.questions.is_multichoice', name='check_multichoice'),
    # url(r'^questions/(?P<question_id>\d+)/sub_questions/new/$', 'survey.views.questions.new_subquestion', name='add_subquestion_page'),
    # url(r'^questions/(?P<question_id>\d+)/sub_questions/edit/$', 'survey.views.questions.edit_subquestion', name='edit_subquestion_page'),
    # """
    url(
        r'^questions/(?P<batch_id>\d+)/new/$',
        'survey.views.questions.new',
        name='new_batch_question_page'),
    url(
        r'^qset/questions/(?P<qset_id>\d+)/new/$',
        'survey.views.set_questions.new',
        name='new_qset_question_page'),
    url(
        r'^qset/questions/(?P<prev_quest_id>\d+)/insert/$',
        'survey.views.set_questions.insert',
        name='insert_qset_question_page'),
    url(
        r'^qset/questions/(?P<question_id>\d+)/loop/$',
        'survey.views.set_questions.manage_loop',
        name='loop_qset_question_page'),
    url(
        r'^question_set/(?P<qset_id>\d+)/questions/$',
        'survey.views.questions.index',
        name='set_questions_index_page'),
    url(
        r'^qset/view_data/(?P<qset_id>\d+)/$',
        'survey.views.question_set.view_data',
        name='view_data_home'),
    url(
        r'^qset/view_listing_data/$',
        'survey.views.question_set.view_listing_data',
        name='view_listing_data'),
    url(
        r'^qset/view_survey_data/$',
        'survey.views.question_set.view_survey_data',
        name='view_survey_data'),
    url(
        r'^qset/view_data/(?P<qset_id>\d+)/$',
        'survey.views.question_set.listing_entries',
        name='listing_entries'),
    url(
        r'^qset/download_data/(?P<qset_id>\d+)/$',
        'survey.views.question_set.download_data',
        name='download_qset_data'),
    url(
        r'^qset/download_attachment/(?P<question_id>\d+/)/(?P<interview_id>\d+/)$',
        'survey.views.question_set.download_attachment',
        name='download_qset_attachment'),
    url(
        r'^listing_form/$',
        'survey.views.survey_listing.index',
        name='%s_home' % ListingTemplate.resolve_tag()),
    url(
        r'^listing_form/new/$',
        'survey.views.survey_listing.new',
        name='new_%s_page' % ListingTemplate.resolve_tag()),
    url(
        r'^listing_form/edit/(?P<qset_id>\d+)/$',
        'survey.views.survey_listing.edit',
        name='edit_%s_page' % ListingTemplate.resolve_tag()),
    url(
        r'^listing_form/delete/(?P<id>\d+)/$',
        'survey.views.survey_listing.delete',
        name='delete_%s' % ListingTemplate.resolve_tag()),
    url(
        r'^qset/delete/(?P<question_id>\d+)/batch/(?P<batch_id>\d+)/$',
        'survey.views.question_set.delete',
        name='delete_qset'),
    url(
        r'^qset/delete/(?P<question_id>\d+)/$',
        'survey.views.question_set.delete_qset_listingform',
        name='delete_qset_listingform'),
    # url(r'^listing_form/qset/(?P<qset_id>\d+)/$',
    #     QuestionSetView(ListingTemplate).assign, name='listing_assign_page'),
    url(
        r'^listing_form/sampling_criteria/(?P<id>\d+)/$',
        'survey.views.survey_listing.index',
        name='sampling_criteria'),
    url(
        r'^questions/(?P<question_id>\d+)/edit/$',
        'survey.views.questions.edit',
        name='edit_question_page'),
    url(
        r'^set_questions/(?P<question_id>\d+)/edit/$',
        'survey.views.set_questions.edit',
        name='qset_edit_question_page'),
    url(
        r'^questions/(?P<question_id>\d+)/sub_questions_json/$',
        'survey.views.questions.get_sub_questions_for_question',
        name='questions_subquestion_json_page'),
    url(
        r'^questions/(?P<question_id>\d+)/prev_questions_json/$',
        'survey.views.questions.get_prev_questions_for_question',
        name='prev_inline_questions_json_page'),
    url(
        r'^questions/(?P<question_id>\d+)/delete/$',
        'survey.views.questions.delete',
        name='delete_question_page'),

    url(
        r'^enumeration_area/new/$',
        'survey.views.enumeration_area.new',
        name='new_enumeration_area_page'),
    url(
        r'^enumeration_area/(?P<ea_id>\d+)/edit/$',
        'survey.views.enumeration_area.edit',
        name='edit_enumeration_area_page'),
    url(
        r'^enumeration_area/(?P<ea_id>\d+)/delete/$',
        'survey.views.enumeration_area.delete',
        name='delete_enumeration_area'),
    url(
        r'^enumeration_area/$',
        'survey.views.enumeration_area.index',
        name='enumeration_area_home'),
    url(
        r'^enumeration_area/filter/$',
        'survey.views.enumeration_area.location_filter',
        name='location_filter'),
    url(
        r'^enumeration_area/sub_types/$',
        'survey.views.enumeration_area.location_sub_types',
        name='location_sub_types'),
    url(
        r'^enumeration_area/ea_filter/$',
        'survey.views.enumeration_area.enumeration_area_filter',
        name='enumeration_area_filter'),
    url(
        r'^enumeration_area/open_surveys/$',
        'survey.views.enumeration_area.open_surveys',
        name='open_surveys_in_ea_area'),
    url(
        r'^modules/new/$',
        'survey.views.question_module.new',
        name='new_question_module_page'),
    url(
        r'^modules/$',
        'survey.views.question_module.index',
        name='question_module_listing_page'),
    url(
        r'^modules/(?P<module_id>\d+)/delete/$',
        'survey.views.question_module.delete',
        name='delete_question_module_page'),
    url(
        r'^modules/(?P<module_id>\d+)/edit/$',
        'survey.views.question_module.edit',
        name='edit_question_module_page'),
    url(
        r'^indicators/new/$',
        'survey.views.indicators.new',
        name='new_indicator_page'),
    url(
        r'^indicators/validate/formulae$',
        'survey.views.indicators.validate_formulae',
        name='validate_formulae'),
    url(
        r'^indicators/$',
        'survey.views.indicators.index',
        name='list_indicator_page'),
    url(
        r'^indicators/variables/$',
        'survey.views.indicators.variables',
        name='indicator_variables'),
    url(
        r'^indicators/(?P<indicator_id>\d+)/formula/new/$',
        'survey.views.indicators.indicator_formula',
        name='add_formula_page'),
    url(
        r'^indicators/(?P<indicator_id>\d+)/variables$',
        'survey.views.indicators.view_indicator_variables',
        name='view_indicator_variables'),
    url(
        r'^indicators/(?P<indicator_id>\d+)/variables/new$',
        'survey.views.indicators.add_indicator_variable',
        name='add_indicator_variable'),
    url(
        r'^indicators/variables/new$',
        'survey.views.indicators.add_variable',
        name='add_variable'),
    url(
        r'^indicators/(?P<indicator_criteria_id>\d+)/variable_condition/delete$',
        'survey.views.indicators.delete_indicator_criteria',
        name='delete_indicator_criteria'),
    url(
        r'^indicators/(?P<variable_id>\d+)/variable/delete$',
        'survey.views.indicators.delete_indicator_variable',
        name='delete_indicator_variable'),
    url(
        r'^indicators/variable/delete$',
        'survey.views.indicators.ajax_delete_indicator_variable',
        name='ajax_delete_indicator_variable'),
    url(
        r'^indicators/(?P<indicator_id>\d+)/download_analysis$',
        'survey.views.indicators.download_indicator_analysis',
        name='download_indicator_analysis'),
    url(
        r'^indicators/(?P<variable_id>\d+)/variables/edit$',
        'survey.views.indicators.edit_indicator_variable',
        name='edit_indicator_variable'),
    url(
        r'^indicators/variables/edit$',
        'survey.views.indicators.ajax_edit_indicator_variable',
        name='ajax_edit_indicator_variable'),
    url(
        r'^indicators/(?P<indicator_id>\d+)/simple/$',
        'survey.views.indicators.simple_indicator',
        name='simple_indicator_chart_page'),
    url(
        r'^indicators/(?P<indicator_id>\d+)/delete/$',
        'survey.views.indicators.delete',
        name='delete_indicator_page'),
    url(
        r'^indicators/(?P<indicator_id>\d+)/edit/$',
        'survey.views.indicators.edit',
        name='edit_indicator_page'),
    url(
        r'^odk/collect/forms/interviews/(?P<submission_id>\d+)/$',
        'survey.odk.views.download_odk_submissions',
        name='download_odk_submission'),
    url(
        r'^odk/collect/forms/instances$',
        'survey.odk.views.instances_form_list',
        name='instances_form_list'),
    url(
        r'^odk/collect/(?P<username>\d+)/(?P<token>[^/]+)/forms$',
        'survey.odk.views.form_list',
        name='odk_survey_forms_list'),
    url(
        r'^odk/collect/forms/(?P<batch_id>\d+)$',
        'survey.odk.views.download_xform',
        name='download_odk_batch_form'),
    url(
        r'^odk/collect/forms$',
        'survey.odk.views.form_list',
        name='odk_survey_forms_list'),
    url(
        r'^odk/collect/forms/listing_form$',
        'survey.odk.views.download_listing_xform',
        name='download_odk_listing_form'),
    url(
        r'^odk/collect/forms/submission$',
        'survey.odk.views.submission',
        name='odk_submit_forms'),
    url(
        r'^odk/aggregate/submission_list/$',
        'survey.odk.views.submission_list',
        name='odk_submission_list'),
    url(
        r'^odk/aggregate/download_attachment/(?P<submission_id>\d+)$',
        'survey.odk.views.download_submission_attachment',
        name='download_submission_attachment'),
    url(
        r'^object_does_not_exist/$',
        login_required(TemplateView.as_view(template_name="empty.html")),
        name='empty_page')
    )

"""
if not settings.PRODUCTION:
    urlpatterns += (
        url(
            r'^api/create_interviewer',
            'survey.views.api.create_interviewer',
            name='create_interviewer'),
        url(
            r'^api/delete_interviewer',
            'survey.views.api.delete_interviewer',
            name='delete_interviewer'),
    )
"""