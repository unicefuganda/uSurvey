from django.forms import widgets
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe


class InlineRadioFieldRenderer(widgets.RadioFieldRenderer):

    def render(self):
        return mark_safe(u'\n %s \n' %
                         u'\n'.join([u' %s &nbsp; ' %
                                     force_unicode(w) for w in self]))


class InlineRadioSelect(widgets.RadioSelect):
    renderer = InlineRadioFieldRenderer
