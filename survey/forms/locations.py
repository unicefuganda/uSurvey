from django import forms
from survey.models import *
from django.forms import ModelForm
from django.core.validators import *
from rapidsms.contrib.locations.models import *
from django.template.defaultfilters import slugify

class LocationTypeForm(ModelForm):

    def clean_name(self):
        name = self.cleaned_data['name']
        types_with_same_name = LocationType.objects.filter(name=name)
        if types_with_same_name and self.initial.get('name', None) != str(name):
            message = "%s already exists" % name
            self._errors['name'] = self.error_class([message])
            del self.cleaned_data['name']
        return name

    def save(self, commit = True, *args, **kwargs):
        a_type = super(LocationTypeForm, self).save(commit = False, *args, **kwargs)
        a_type.slug = slugify(a_type.name)
        if commit:
            a_type.save()

        return a_type


    class Meta:
        model = LocationType
        exclude = ['slug']


