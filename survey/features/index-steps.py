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

def visit(url):
  world.browser.visit(django_url(url))

@step(u'Given I access the url "([^"]*)"')
def given_i_access_the_url_group1(step, group1):
    try:
        visit("/")
    except Exception, e:
        assert type(e).__name__ +":"+ str(e) == "HttpResponseError:404 - Not Found"
