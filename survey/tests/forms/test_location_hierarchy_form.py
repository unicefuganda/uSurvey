from django.forms.formsets import formset_factory
from django.template.defaultfilters import slugify
from django.test.testcases import TestCase
from rapidsms.contrib.locations.models import Location, LocationType
from survey.forms.location_details import LocationDetailsForm
from survey.forms.location_hierarchy import LocationHierarchyForm, BaseArticleFormSet
from survey.models import LocationTypeDetails


class LocationHierarchyFormTest(TestCase):
    def setUp(self):
        country = LocationType.objects.create(name='country',slug=slugify('country'))
        self.uganda = Location.objects.create(type=country, name='Uganda')

    def test_knows_the_fields_in_form(self):
        hierarchy_form = LocationHierarchyForm()

        fields = ['country']
        [self.assertIn(field, hierarchy_form.fields) for field in fields]

    def test_should_populate_countries_name(self):
        hierarchy_form = LocationHierarchyForm()

        field = 'country'
        all_countries = Location.objects.filter(type__name='country')
        country_choices = hierarchy_form.fields[field].choices

        [self.assertIn((country_option.id, country_option.name), country_choices) for country_option in all_countries]

    def test_should_populate_countries_name_case_insensitive(self):
        LocationType.objects.all().delete()
        Location.objects.all().delete()
        country_1 = LocationType.objects.create(name='Country',slug=slugify('Country'))
        some_country = Location.objects.create(type=country_1, name='some_country')

        field = 'country'
        hierarchy_form = LocationHierarchyForm()
        all_countries = Location.objects.filter(type__name='country')
        country_choices = hierarchy_form.fields[field].choices

        [self.assertIn((country_option.id, country_option.name), country_choices) for country_option in all_countries]
        self.assertIn((some_country.id, some_country.name), country_choices)

    def test_should_not_be_valid_if_country_is_blank(self):
        data = {
            'country':'',
            'levels': 'Region'
        }
        hierarchy_form = LocationHierarchyForm(data=data)
        self.assertFalse(hierarchy_form.is_valid())

    def test_form_set_has_error_if_has_code_is_on_but_no_code_supplied(self):
        DetailsFormSet = formset_factory(LocationDetailsForm, formset=BaseArticleFormSet)

        data = {'form-0-levels': 'Region', 'form-MAX_NUM_FORMS': '1000', 'form-0-required': 'on',
                'form-TOTAL_FORMS': '1', 'form-0-code': '', 'form-INITIAL_FORMS': '0',
                'form-0-has_code': 'on'}

        details_formset = DetailsFormSet(data,prefix='form')
        message = "Code cannot be blank if has code is checked."

        self.assertFalse(details_formset.is_valid())

        self.assertIn(message, details_formset.forms[0].errors['code'])

    def test_should_show_used_country_as_available_choices_if_any_otherwise_show_all_countries(self):
        other_country = Location.objects.create(name="some other country", type=self.uganda.type)
        LocationTypeDetails.objects.create(required=True,has_code=False, location_type=self.uganda.type, country=self.uganda)
        hierarchy_form = LocationHierarchyForm()

        field = 'country'
        country_choices = hierarchy_form.fields[field].choices

        self.assertEqual(1, len(country_choices))
        self.assertEqual((self.uganda.id, self.uganda.name), country_choices[0])
