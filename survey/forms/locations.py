from django import forms
from django.forms import ModelForm
from rapidsms.contrib.locations.models import *

from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError

from survey.models.formula import *


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


class LocationForm(ModelForm):

    def editing_instance(self, cleaned_data):
        for field in cleaned_data.keys():
            if self.initial.get(field, None) != cleaned_data[field]:
                return False
        return True

    def clean_type(self):
        a_type = self.cleaned_data['type']
        if not a_type:
            message = "This field is required."
            self._errors['type'] = self.error_class([message])
            del self.cleaned_data['type']
        return a_type

    def clean(self):
        cleaned_data = super(LocationForm, self).clean()
        locations_with_same_attributes = Location.objects.filter(**cleaned_data)
        if locations_with_same_attributes and not self.editing_instance(cleaned_data):
            raise ValidationError('This location already exists.')
        return cleaned_data

    class Meta:
        model = Location
        exclude = ['point', 'parent_type', 'parent_id']
        widgets = {
            'tree_parent': forms.Select(attrs={'class':'chzn-select', 'data-placeholder':'Select or Type District'}),
            }