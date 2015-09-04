__author__ = 'anthony'
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

content_type = ContentType.objects.get_for_model(User)
permission = Permission.objects.create(codename='can_enter_data', name='Can enter data', content_type=content_type)
permission = Permission.objects.create(codename='can_view_batches', name='Can view Batches', content_type=content_type)