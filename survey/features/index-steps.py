# -*- coding: utf-8 -*-
from lettuce import *
from splinter import Browser
from lettuce.django import django_url
from django.core.management import call_command
from survey.models import Backend
from django.conf import settings

@before.each_scenario
def flush_database(step):
    call_command('flush', interactive=False)
    create_backends()

@before.each_scenario
def open_browser(step):
    world.browser = Browser()

@after.each_scenario
def close_browser(step):
    world.browser.quit()

def create_backends():
    for backend in settings.INSTALLED_BACKENDS.keys():
        Backend.objects.get_or_create(name=backend)