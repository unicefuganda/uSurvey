import string
import re
from collections import OrderedDict
from cacheops import cached_as
from django import template
from django.core.urlresolvers import reverse
from django.conf import settings
from survey.interviewer_configs import MONTHS
from survey.models.helper_constants import CONDITIONS
from survey.utils.views_helper import get_ancestors
from survey.models import Survey, Question, Batch, Interviewer, MultiChoiceAnswer, \
    GroupCondition, Answer, AnswerAccessDefinition, ODKAccess, HouseholdMember, SurveyAllocation
from survey.models import VideoAnswer, AudioAnswer, ImageAnswer, QuestionSet
from survey.odk.utils.log import logger
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from dateutil import relativedelta
from datetime import date
import json
import inspect
from django.utils import html
from survey.forms.logic import LogicForm
import redis

store = redis.Redis()

register = template.Library()


@register.filter
def current(value, arg):
    try:
        return value[int(arg)]
    except:
        return None


@register.filter
def next(value, arg):
    try:
        return value[int(arg) + 1]
    except:
        return None




@register.filter
def space_replace(value, search_string):
    return value.replace(search_string, ' ')


@register.filter
def replace_space(value, replace_string):
    """Basically the inverse of space replace
    :param value:
    :param replace_string:
    :return:
    """
    return value.replace(' ', replace_string)



@register.filter
def is_location_selected(locations_data, location):
    if locations_data.has_location_selected(location):
        return "selected='selected'"


@register.filter
def is_ea_selected(locations_data, ea):
    if locations_data.selected_ea == ea:
        return "selected='selected'"


@register.filter
def is_selected(batch, selected_batch):
    if batch == selected_batch:
        return "selected='selected'"


@register.filter
def is_batch_open_for_location(open_locations, location):
    if location in open_locations:
        return "checked='checked'"


@register.filter
def is_mobile_number(field):
    return 'mobile number' in field.lower()


@register.filter
def is_radio(field):
    if "radio" in str(field) and not "select" in str(field):
        return "radio_field"
    return ""


@register.filter
def display_list(list):
    new_list = [str(item) for item in list]
    return mark_safe(', '.join(new_list))


@register.filter
def join_list(list, delimiter):
    new_list = ['<span class="muted">%s</span>' % string.capwords(str(item)) for item in list]
    return mark_safe(delimiter.join(new_list))


@register.filter
def get_value(dict, key):
    return dict.get(key, "")


@register.filter
def get_cached_result(key, default):
    return cache.get(key, default)


@register.filter
def batches_enabled(survey, ea):
    return 'Enabled' if survey.batches_enabled(ea) else 'Not Enabled'


@register.filter
def get_month(index):
    if not str(index).isdigit() and not index:
        return "N/A"
    return MONTHS[int(index)][1]


@register.filter
def format_date(date):
    if date:
        return date.strftime("%b %d, %Y")


@register.filter
def get_age(d):
    return relativedelta.relativedelta(date.today(), d).years


@register.filter
def get_url_with_ids(args, url_name):
    if not str(args).isdigit():
        arg_list = [int(arg) for arg in args.split(',')]
        return reverse(url_name, args=arg_list)
    if isinstance(args, dict):
        reverse(url_name, kwargs=args)
    return reverse(url_name, args=(args,))


@register.filter
def get_url_without_ids(url_name):
    return reverse(url_name)


@register.filter
def add_string(int_1, int_2):
    return "%s, %s" % (str(int_1), str(int_2))


@register.assignment_tag
def concat_strings(*args):
    return ''.join([str(arg) for arg in args])


@register.filter
def condition_text(key):
    value = CONDITIONS.get(key, "")
    return value


@register.filter
def modulo(num, val):
    return num % val == 0


@register.filter
def repeat_string(s, times):
    return s * (times - 1)


@register.filter
def is_survey_selected_given(survey, selected_batch):
    if not selected_batch or not selected_batch.survey:
        return None

    if survey == selected_batch.survey:
        return "selected='selected'"


@register.filter
def non_response_is_activefor(open_locations, location):
    if location in open_locations:
        return "checked='checked'"


@register.filter
def ancestors_reversed(location):
    ancestors = get_ancestors(location)
    ancestors.reverse()
    return ancestors


@register.filter
def show_condition(flow):
    if flow.validation_test:
        return '%s ( %s )' % (flow.validation_test, ' and '.join(flow.test_arguments))
    return ""


@register.filter
def access_channels(answer_type):
    channels = AnswerAccessDefinition.objects.filter(
        answer_type=answer_type).values_list('channel', flat=True).order_by('channel')
    return ",".join(channels)


@register.filter
def quest_validation_opts(batch):
    opts_dict = {}
    for cls in Answer.__subclasses__():
        opts = []
        for validator in cls.validators():
            opts.append({'display': validator.__name__,
                         'value': validator.__name__.upper()})
        opts_dict[cls.choice_name()] = opts
    return mark_safe(json.dumps(opts_dict))


@register.filter
def validation_args(batch):
    args_map = {}
    for validator in Answer.validators():
        args_map.update({validator.__name__.upper(): len(inspect.getargspec(
            validator).args) - 2})  # validator is a class method, plus answer extra pram
    return mark_safe(json.dumps(args_map))


@register.filter
def trim(value):
    return value.strip()


@register.filter
def household_completed_percent(interviewer):
    households = interviewer.households.all()
    total = households.count()
    completed = len([hld for hld in households.all(
    ) if not hld.survey_completed() and hld.household_member.count() > 0])
    if total > 0:
        return "%s%%" % str(completed * 100 / total)


@register.assignment_tag
def get_answer(question, interview):
    @cached_as(question, interview)
    def _get_answer():
        answer_class = Answer.get_class(question.answer_type)
        try:
            if answer_class in [VideoAnswer, AudioAnswer, ImageAnswer]:
                return mark_safe('<a href="{% url download_qset_attachment %s %s %}">Download</a>' % (question.pk,
                                                                                                      interview.pk))
            else:
                return answer_class.get(interview=interview, question=question).value
        except answer_class.DoesNotExist:
            return ''
    return _get_answer()


@register.assignment_tag
def can_start_survey(interviewer):
    return SurveyAllocation.can_start_batch(interviewer)


@register.filter
def open_survey_in_current_loc(interviewer):
    return len(Survey.currently_open_surveys(interviewer.location))


@register.filter
def households_for_open_survey(interviewer):
    open_survey = Survey.currently_open_surveys(interviewer.location)
    households = interviewer.households.filter(survey__in=open_survey).all()
    return len([hs for hs in households if hs.get_head() is not None])


@register.filter
def total_household_members(interviewer):
    households = interviewer.households.all()
    return sum([household.household_member.count() for household in households])


@register.assignment_tag
def has_super_powers(request):
    from survey.utils.views_helper import has_super_powers
    return has_super_powers(request)


@register.assignment_tag
def is_relevant_sample(ea_id, assignments):
    ea_assignmts = assignments.filter(allocation_ea__id=ea_id)
    return ' or '.join(["selected(/qset/surveyAllocation, '%s')" % a.pk for a in ea_assignmts ])


@register.assignment_tag
def get_download_url(request, url_name, instance=None):
    if instance is None:
        return request.build_absolute_uri(reverse(url_name))
    else:
        return request.build_absolute_uri(reverse(url_name, args=(instance.pk, )))


@register.assignment_tag
def get_sample_data_display(sample):
    survey = sample.survey
    naming_label = survey.random_sample_label
    interview = sample.interview
    # get the exact answer type
    pattern = '{{ *([0-9a-zA-Z_]+) *}}'
    identifiers = re.findall(pattern, naming_label)
    questions = survey.listing_form.questions.filter(identifier__in=identifiers)
    context = {}
    for question in questions:
        answer_class = Answer.get_class(question.answer_type)
        try:
            answer = answer_class.get(interview=interview, question=question)
            context[question.identifier] = answer.value
        except answer_class.DoesNotExist:
            pass
    question_context = template.Context(context)
    return template.Template(html.escape(naming_label)).render(question_context)

@register.assignment_tag
def get_odk_mem_question(question):
    surname = HouseholdMember._meta.get_field('surname')
    first_name = HouseholdMember._meta.get_field('first_name')
    gender = HouseholdMember._meta.get_field('gender')
    context = {
        surname.verbose_name.upper().replace(' ', '_'):
        mark_safe('<output value="/survey/household/householdMember/surname"/>'),
        first_name.verbose_name.upper().replace(' ', '_'):
        mark_safe('<output value="/survey/household/householdMember/firstName"/>'),
        gender.verbose_name.upper().replace(' ', '_'):
            mark_safe('<output value="/survey/household/householdMember/sex"/>'),
    }
    question_context = template.Context(context)
    return template.Template(html.escape(question.text)).render(question_context)


@register.assignment_tag
def get_loop_aware_path(question):
    loops = question.qset.get_loop_story().get(question.pk, [])
    tokens = ['q%sq%s' % (loop.loop_starter.pk, loop.loop_ender.pk) for loop in loops]
    if tokens:
        return '/%s' % '/'.join(tokens)
    else:
        return ''


def get_xform_relative_path(question):
    return '/qset/qset%s/questions/surveyQuestions%s' % (question.qset.pk, get_loop_aware_path(question))


def get_node_path(question):
    return '%s/q%s' % (get_xform_relative_path(question), question.pk)


@register.assignment_tag(takes_context=True)
def is_relevant_odk(context, question, interviewer):
    batch = question.qset
    if question.pk == batch.start_question.pk:
        default_relevance = 'true()'
    else:
        default_relevance = 'false()'
    relevance_context = ' (%s)' % (
        ' or '.join(context.get(question.pk, [default_relevance, ])),
    )
    if hasattr(question, 'group'):
        relevance_context = '%s %s' % (relevance_context, is_relevant_by_group(context, question))

    # do not include back to flows to this
    flows = question.flows.exclude(desc=LogicForm.BACK_TO_ACTION)
    node_path = get_node_path(question)
    flow_conditions = []
    if flows:
        for flow in flows:
            if flow.validation_test:
                text_params = [t.param for t in flow.text_arguments]
                answer_class = Answer.get_class(question.answer_type)
                flow_condition = answer_class.print_odk_validation(     # get appropriate flow condition
                    node_path, flow.validation_test, *text_params)
                flow_conditions.append(flow_condition)
                if flow.next_question:
                    next_question = flow.next_question
                    next_q_context = context.get(
                        next_question.pk, ['false()', ])
                    next_q_context.append(flow_condition)
                    context[next_question.pk] = next_q_context
        null_flows = flows.filter(
            validation_test__isnull=True, next_question__isnull=False)
        if null_flows:
            null_flow = null_flows[0]
            # check if next question if we are moving to a less looped question
            # essentially same as checking if next question is outside current questions loop
            loop_story = question.qset.get_loop_story()
            if len(loop_story.get(question.pk, [])) > len(loop_story.get(null_flow.next_question.pk, [])):
                null_condition = ["count(%s) &gt; 0" % node_path, ]
            else:
                null_condition = ["string-length(%s) &gt; 0" % node_path, ]
            # ['true()', "string-length(%s) &gt; 0" % node_path]
            # null_condition = ['true()', ]
            if len(flow_conditions) > 0 and hasattr(question, 'loop_ended') is False:
                null_condition.append('not(%s)' %
                                      ' or '.join(flow_conditions))
            next_question = null_flow.next_question
            next_q_context = context.get(next_question.pk, ['false()', ])
            next_q_context.append('(%s)' % ' and '.join(null_condition))
            if hasattr(question, 'group') and (hasattr(next_question, 'group') is False or
                                                       question.group != next_question.group):
                next_q_context.append('true()')
            # if get_loop_aware_path(question) != get_loop_aware_path(next_question):
            #     next_q_context.append('true()')
            # if hasattr(next_question, 'loop_ended'):
            #     next_q_context.append('true()')
            context[next_question.pk] = next_q_context
    return mark_safe(relevance_context)


def get_group_question_path(qset, group_question):
    return '/qset/qset%s/questions/groupQuestions/q%s' % (qset.id, group_question.id)


def is_relevant_by_group(context, question):
    question_group = question.group
    qset = question.qset

    @cached_as(question_group, qset)
    def _is_relevant_by_group(qset):
        qset = QuestionSet.get(pk=qset.pk)
        relevant_new = []
        for condition in question_group.group_conditions.all():
            test_question = qset.parameter_list.questions.get(identifier=condition.test_question.identifier)
            answer_class = Answer.get_class(condition.test_question.answer_type)
            relevant_new.append(answer_class.print_odk_validation(get_group_question_path(qset, test_question),
                                                                  condition.validation_test,  *condition.test_params))
        relevance_builder = ['false()', ]
        if relevant_new:
            relevance_builder.append('(%s)' % ' and '.join(relevant_new))
        return ' and (%s)' % ' or '.join(relevance_builder)
    return _is_relevant_by_group(qset)
