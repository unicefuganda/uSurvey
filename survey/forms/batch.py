from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models import Batch, BatchChannel
from django.utils.safestring import mark_safe

from survey.models.formula import *


class BatchForm(ModelForm):
    access_channels = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                         choices=BatchChannel.ACCESS_CHANNELS)
    
    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            initial = kwargs.setdefault('initial', {})
            initial['access_channels'] = [c.channel for c in kwargs['instance'].access_channels.all()]
        forms.ModelForm.__init__(self, *args, **kwargs)        

    class Meta:
        model = Batch
        fields = ['name', 'description', 'survey', ]

        widgets = {
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50}),
            'survey' : forms.HiddenInput(),
        }


    def save(self, commit=True, **kwargs):
        batch = super(BatchForm, self).save(commit=commit)
        bc = BatchChannel.objects.filter(batch=batch)
        bc.delete()
        for val in kwargs['access_channels']:
           BatchChannel.objects.create(batch=batch, channel=val)
