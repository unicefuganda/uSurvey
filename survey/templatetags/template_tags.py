from django import template
from django.core.urlresolvers import reverse
from survey.investigator_configs import MONTHS
from survey.models.helper_constants import CONDITIONS
from survey.utils.views_helper import get_ancestors
from survey.models import Survey, Question, Batch, Investigator, MultiChoiceAnswer, GroupCondition
from survey.odk.utils.log import logger
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from dateutils import relativedelta
from datetime import date

register = template.Library()

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
    return ', '.join(new_list)

@register.filter
def get_value(dict, key):
    return dict.get(key, "")

@register.filter
def get_month(index):
    if not str(index).isdigit() and not index :
        return "N/A"
    return MONTHS[int(index)][1]

@register.filter
def format_date(date):
    return date.strftime("%b %d, %Y")

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
def household_completed_percent(investigator):
#    import pdb;pdb.set_trace()
    households = investigator.households.all()
    total = households.count()
    completed = len([hld for hld in households.all() if not hld.survey_completed() and hld.household_member.count() > 0])
    if total > 0:
        return "%s%%" % str(completed*100/total)

@register.filter
def open_survey_in_current_loc(investigator):
    return len(Survey.currently_open_surveys(investigator.location)) 
    
@register.filter
def households_for_open_survey(investigator):
    open_survey = Survey.currently_open_surveys(investigator.location)
    households = investigator.households.filter(survey__in=open_survey).all()
    return len([hs for hs in households if hs.get_head() is not None])

@register.filter
def total_household_members(investigator):
    households = investigator.households.all()
    return sum([household.household_member.count() for household in households])

@register.assignment_tag(takes_context=True)
def clean_odk_relevant_context(context, question, batch, investigator):
    relevant_q = context.get('relevant_q', {})
    relevant_q.pop(question.pk, None) #if it happens that this is skip to question of a previous one remove it in context
    context['relevant_q'] = relevant_q
    return ''

@register.assignment_tag(takes_context=True)
def is_relevant_odk(context, question, batch, investigator, registered_households):
    skip_to_ques = context.get('skip_to_ques', {})
    skip_to_ques.pop(question.pk, None)
    sub_ques = context.get('sub_ques', {})
    terminal_ques = context.get('terminal_ques', [])
    relevance_context = '%s %s %s %s' % (
                                   ' '.join(sub_ques.pop(question.pk, [])),
                                   ' '.join([test for test in skip_to_ques.values() if test.find('/survey/b%s/' % batch.pk) > -1]),
                                   ' '.join([test for test in terminal_ques if test.find('/survey/b%s/' % batch.pk) > -1]),
                                   is_relevant_by_group(question, registered_households)
                                   )
    if question.answer_type.lower() == 'multichoice' and question.rule.count():
        for option in question.options.all():
            answer = MultiChoiceAnswer()
            answer.investigator = investigator
            answer.batch = batch
            answer.question = question
            answer.answer = option
            try:
                next_question = question.get_odk_next_question(answer)
                if next_question is not None:
                    action = next_question.parent_question_rules.get(validate_with_option=answer.answer).action
                    if action == 'SKIP_TO':
                        skip_to_ques[next_question.pk] = " and not(selected(/survey/b%s/q%s,'%s'))" % (batch.pk, question.pk, option.pk)
                    if action =='ASK_SUBQUESTION':
                        fellows = sub_ques.get(next_question.pk, [])
                        fellows.append(" and selected(/survey/b%s/q%s,'%s')" % (batch.pk, question.pk, option.pk))
                        sub_ques[next_question.pk] = fellows
                else:
                    terminal_ques.append(" and not(selected(/survey/b%s/q%s,'%s'))" % (batch.pk, question.pk, option.pk))
            except ObjectDoesNotExist, e:
                pass
#    else:
        
            #import pdb; pdb.set_trace()
    context['skip_to_ques'] = skip_to_ques
    context['sub_ques'] = sub_ques    
    context['terminal_ques'] = terminal_ques
    return mark_safe(relevance_context)


def is_relevant_by_group(question, registered_households):
    question_group = question.group
    relevant_new = []
    extra = ''
    if question_group.name == 'GENERAL':
        relevant_new.append(" selected(/survey/household/householdMember/isHead,'1')")
    MATCHING_METHODS = {
            'EQUALS': '=',
            'GREATER_THAN': '&gt;',
            'LESS_THAN': '&lt;',
    }
    for group_condition in question_group.get_all_conditions():
        method = MATCHING_METHODS.get(group_condition.condition, None)
        value = group_condition.value
        if method is not None:
            if group_condition.attribute == GroupCondition.GROUP_TYPES['AGE']:
                today = date.today()
                age_date = today - relativedelta(years=int(value))
                age_date_str = date.strftime(age_date, '%Y-%m-%d')
                relevant_new.append(" (date('%s') %s /survey/household/householdMember/dateOfBirth)" % (age_date_str, method))
            if group_condition.attribute == GroupCondition.GROUP_TYPES['GENDER']:
                is_male = '0'
                if str(value).lower() == "male" or str(value) == str(True):
                    is_male = '1'
                relevant_new.append(" selected(/survey/household/householdMember/sex, '%s')" % is_male)

    relevant_existing = []
    for household in registered_households:
        for member in household.all_members():
            if member.belongs_to(question_group):
                relevant_existing.append(" /survey/registeredHousehold/selectedMember = '%s' " % member.pk)
    relevance_builder = []
    if relevant_new:
        relevance_builder.append('(%s)' % ' and '.join(relevant_new))
    existing = ''
    if relevant_existing:
        relevance_builder.append('(%s)' %  ' or '.join(relevant_existing))
    if relevance_builder:
        return ' and (%s)' % ' or '.join(relevance_builder))
    else: return ''

    

