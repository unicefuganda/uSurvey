mics
====

Installation
------------
* Postgres, rabbitmq and memcached should be running
(on OSX  install memcached and libmemcached from brew)

##Git

        git clone https://github.com/unicefuganda/mics.git
        (adjust localsettings.py for db setup)

        cd mics

        mkvirtualenv mics

        pip install -r pip-requires.txt

        python manage.py syncdb --noinput

        python manage.py migrate

        python manage.py runserver

==

* run test and harvest

        python manage.py test

Done!! you're good to go :)

Filenaming convention:
----------------------
* for tests: test_[[OBJECT]]_[[ACTION]].py
e.g: test_location_form.py, test_location_model.py, test_location_views.py

====


[![Build Status](https://travis-ci.org/unicefuganda/mics.png?branch=master)](https://travis-ci.org/unicefuganda/mics)
[![Coverage Status](https://coveralls.io/repos/unicefuganda/mics/badge.png)](https://coveralls.io/r/unicefuganda/mics)