# -*- coding: utf-8 -*-
from lettuce import *
from splinter import Browser
from lettuce.django import django_url
from django.core.management import call_command
from survey.models import Backend
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.template.defaultfilters import slugify
import glob

@before.each_scenario
def flush_database(step):
    Permission.objects.all().delete()
    call_command('flush', interactive=False)
    create_backends()

@before.all
def clear_screenshots():
    screenshots = glob.glob('./screenshots/*.png')
    for screenshot in screenshots:
        os.remove(screenshot)

@before.each_scenario
def open_browser(step):
    world.browser = Browser()

@after.each_scenario
def close_browser(scenario):
    if scenario.failed:
        world.browser.driver.save_screenshot('screenshots/%s.png' % slugify(scenario.name))
    world.browser.quit()

def create_backends():
    for backend in settings.INSTALLED_BACKENDS.keys():
        Backend.objects.get_or_create(name=backend)