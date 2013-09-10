from django.forms import ModelForm

from survey.models.question import Question
from survey.models.householdgroups import HouseholdMemberGroup

class QuestionForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['answer_type'].choices = list(Question.TYPE_OF_ANSWERS)
        self.fields['group'].choices = [(group.id, group.name) for group in HouseholdMemberGroup.objects.all()]

    class Meta:
        model = Question
        fields =['text', 'answer_type', 'group']
