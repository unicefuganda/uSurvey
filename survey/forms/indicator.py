from django.forms import ModelForm
from survey.models import Indicator, Batch, QuestionModule


class IndicatorForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(IndicatorForm, self).__init__(*args, **kwargs)
        self.fields['batch'].choices = map(lambda batch: (batch.id, batch.name), Batch.objects.all())
        self.fields['module'].choices = map(lambda module: (module.id, module.name), QuestionModule.objects.all())

    class Meta:
        model = Indicator