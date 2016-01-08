from django import template
from django.core.urlresolvers import reverse
from survey.interviewer_configs import MONTHS
from survey.models.helper_constants import CONDITIONS
from survey.utils.views_helper import get_ancestors
from survey.models import Survey, Question, Batch, Interviewer, MultiChoiceAnswer, \
    GroupCondition, Answer, AnswerAccessDefinition, ODKAccess, HouseholdMember
from survey.odk.utils.log import logger
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from dateutil import relativedelta
from datetime import date
import json, inspect
from django.utils import html

register = template.Library()

@register.filter
def next(value, arg):
    try:
        return value[int(arg)+1]
    except:
        return None

@register.filter
def space_replace(value, search_string):
    return value.replace(search_string, ' ')


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
    new_list = ['<span class="muted">%s</span>' % str(item) for item in list]
    return mark_safe(delimiter.join(new_list))

@register.filter
def get_value(dict, key):
    return dict.get(key, "")

@register.filter
def batches_enabled(survey, ea):
    return 'Enabled' if survey.batches_enabled(ea) else 'Not Enabled'

@register.filter
def get_month(index):
    if not str(index).isdigit() and not index :
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
    return reverse(url_name, args=(args,))    

@register.filter
def get_url_without_ids(url_name):
    return reverse(url_name)    

@register.filter
def add_string(int_1, int_2):
    return "%s, %s"%(str(int_1), str(int_2))

@register.filter
def condition_text(key):
    value = CONDITIONS.get(key, "")
    return value

@register.filter
def modulo(num, val):
    return num % val == 0

@register.filter
def repeat_string(string, times):
    return string*(times-1)

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
    channels = AnswerAccessDefinition.objects.filter(answer_type=answer_type).values_list('channel', flat=True).order_by('channel')
    return ",".join(channels)

@register.filter
def quest_validation_opts(batch):
    opts_dict = {}
    for cls in Answer.__subclasses__():
        opts = []
        for validator in cls.validators():
            opts.append({'display': validator.__name__, 'value': validator.__name__.upper() })
        opts_dict[cls.choice_name()] = opts
    return mark_safe(json.dumps(opts_dict));

@register.filter
def validation_args(batch):
    args_map = {}
    for validator in Answer.validators():
        args_map.update({validator.__name__.upper() : len(inspect.getargspec(validator).args) - 2 }) #validator is a class method, plus answer extra pram
    return mark_safe(json.dumps(args_map));
        
@register.filter
def trim(value):
    return value.strip()
    

@register.filter
def household_completed_percent(interviewer):
#    import pdb;pdb.set_trace()
    households = interviewer.households.all()
    total = households.count()
    completed = len([hld for hld in households.all() if not hld.survey_completed() and hld.household_member.count() > 0])
    if total > 0:
        return "%s%%" % str(completed*100/total)

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
def  get_download_url(request, url_name, instance=None):
    if instance is None:
        return request.build_absolute_uri(reverse(url_name))
    else:
        return request.build_absolute_uri(reverse(url_name, args=(instance.pk, )))

@register.assignment_tag
def  get_odk_mem_question(question):
    surname = HouseholdMember._meta.get_field('surname')
    first_name = HouseholdMember._meta.get_field('first_name')
    gender = HouseholdMember._meta.get_field('gender')
    context = {
        surname.verbose_name.upper().replace(' ', '_') :
                mark_safe('<output value="/survey/household/householdMember/surname"/>'),
        first_name.verbose_name.upper().replace(' ', '_') :
                mark_safe('<output value="/survey/household/householdMember/firstName"/>'),
        gender.verbose_name.upper().replace(' ', '_') :
            mark_safe('<output value="/survey/household/householdMember/sex"/>'),
    }
    question_context = template.Context(context)
    return template.Template(html.escape(question.text)).render(question_context)


@register.assignment_tag(takes_context=True)
def is_relevant_odk(context, question, interviewer, registered_households):
    batch = question.batch
    if question.pk == batch.start_question.pk:
        default_relevance = 'true()'
    else:
        default_relevance = 'false()'
    relevance_context = ' (%s) %s' % (
                                ' or '.join(context.get(question.pk, [default_relevance, ])),
                                is_relevant_by_group(context, question, registered_households)
                                )
    flows = question.flows.all()
    node_path = '/survey/b%s/q%s' % (batch.pk, question.pk)
    flow_conditions = []
    if flows:
        for flow in flows:
            if flow.next_question:
                next_question = flow.next_question
                next_q_context = context.get(next_question.pk, ['false()', ])
                if flow.validation_test:
                    text_params = [t.param for t in flow.text_arguments]
                    answer_class = Answer.get_class(question.answer_type)
                    flow_condition = answer_class.print_odk_validation(node_path, flow.validation_test, *text_params)
                    flow_conditions.append(flow_condition)
                    next_q_context.append(flow_condition)
                    context[next_question.pk] = next_q_context
            # else:

        null_flows = flows.filter(validation_test__isnull=True, next_question__isnull=False)
        if null_flows:
            null_flow = null_flows[0]
            null_condition = ["string-length(%s) &gt; 0" % node_path, ]
            # null_condition = ['true()', ]
            if len(flow_conditions) > 0:
                null_condition.append('not (%s)' % ' or '.join(flow_conditions))
            next_question = null_flow.next_question
            next_q_context = context.get(next_question.pk, ['false()', ])
            next_q_context.append('(%s)' % ' and '.join(null_condition))
            context[next_question.pk] = next_q_context
            if null_flow.next_question and question.group != null_flow.next_question.group:
                prob_next = batch.next_inline(null_flow.next_question,
                                              exclude_groups=[null_flow.next_question.group, ])
                if prob_next:
                    prob_next_context = context.get(prob_next.pk, ['false()', ])
                    prob_next_context.append("string-length(%s) &gt; 0" % node_path)
                    context[prob_next.pk] = prob_next_context
    return mark_safe(relevance_context)


def is_relevant_by_group(context, question, registered_households):
    question_group = question.group
    relevant_existing = []
    relevant_new = []
    attributes = {
                  'AGE': '/survey/household/householdMember/age',
                  'GENDER': '/survey/household/householdMember/sex',
                  'GENERAL': '/survey/household/householdMember/isHead'
                }
    for condition in question_group.get_all_conditions():
        relevant_new.append(condition.odk_matches(attributes))

    # for household in registered_households:
    #     for member in household.members.all():
    #         if member.belongs_to(question_group):
    #             relevant_existing.append(" /survey/registeredHousehold/selectedMember = '%s_%s' " % (member.household.pk, member.pk))
    #         else:
    #         #get next inline question... This is another flow leading to the next inline question in case current is not applicable
    #             connecting_flows = question.connecting_flows.filter(validation_test__isnull=True)
    #             if connecting_flows:
    #                 f_question = connecting_flows[0].question
    #                 next_question = f_question.batch.next_inline(f_question, groups=member.groups,
    #                                                                         channel=ODKAccess.choice_name())
    #                 if next_question:
    #                     node_path = '/survey/b%s/q%s' % (f_question.batch.pk, f_question.pk)
    #                     next_q_context = context.get(next_question.pk, ['false()', ])
    #                     next_q_context.append("string-length(%s) &gt; 0" % node_path)
    #                     context[next_question.pk] = next_q_context
    relevance_builder = ['false()', ]
    if relevant_new:
       relevance_builder.append('(%s)' % ' and '.join(relevant_new))
    if relevant_existing:
        relevance_builder.append('(%s)' % ' or '.join(relevant_existing))
    return ' and (%s)' % ' or '.join(relevance_builder)

    

