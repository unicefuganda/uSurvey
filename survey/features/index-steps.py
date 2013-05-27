# -*- coding: utf-8 -*-
from lettuce import *
from splinter import Browser
from lettuce.django import django_url

@before.each_scenario
def open_browser(step):
    world.browser = Browser()

@after.each_scenario
def close_browser(step):
    world.browser.quit()