__author__ = 'anthony <>'
from collections import OrderedDict
from django import forms


class FormOrderMixin(object):

    def order_fields(self, field_order):
        """
        Rearranges the fields according to field_order.
        field_order is a list of field names specifying the order. Fields not
        included in the list are appended in the default order for backward
        compatibility with subclasses not overriding field_order. If field_order
        is None, all fields are kept in the order defined in the class.
        Unknown fields in field_order are ignored to allow disabling fields in
        form subclasses without redefining ordering.
        """
        if field_order is None:
            return
        fields = OrderedDict()
        for key in field_order:
            try:
                fields[key] = self.fields.pop(key)
            except KeyError:  # ignore unknown fields
                pass
        fields.update(self.fields)  # add remaining fields in original order
        self.fields = fields


def get_form_field_no_validation(fieldname):
    class FieldNoValidation(fieldname):

        def clean(self, value):
            return value

    return FieldNoValidation


class Icons(object):

    icons = {}

