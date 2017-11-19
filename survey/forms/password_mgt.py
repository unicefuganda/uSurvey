#!/usr/bin/env python
__author__ = 'anthony <antsmc2@gmail.com>'

from django.contrib.auth.forms import PasswordResetForm


class uSurveyPasswordResetForm(PasswordResetForm):
    """Would have just enabled is_admin_site in auth password reset view. But seems that would be depreciated in 1.10
    """
    def save(self, **kwargs):
        """Just over ridden to det default domain
        """
        kwargs['domain_override'] = kwargs['request'].get_host()
        return super(uSurveyPasswordResetForm, self).save(**kwargs)
