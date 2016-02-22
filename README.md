mics
====

Installation
------------
* Postgres, redis-server should be running

##Git

        git clone https://github.com/unicefuganda/mics.git

        cd mics/mics

        cp localsettings.py.example localsettings.py
        (adjust localsettings.py for db and test_db setup)

        cd ../survey

        cp interviewer_configs.py.example interviewer_configs.py

        cd ..

        mkvirtualenv mics

        pip install -r pip-requires.txt

        python manage.py syncdb --noinput

        python manage.py migrate

        python manage.py runserver

==

* run test

        python manage.py test

* run lettuce test
adjust testsettings for test_db setup
first install phantomjs if not already installed (brew install phantomjs in OSX).

        python manage.py syncdb --settings=mics.testsettings
        python manage.py migrate --settings=mics.testsettings
        python manage.py harvest

Done!! you're good to go :)

Filenaming convention:
----------------------
* for tests: test_[[OBJECT]]_[[ACTION]].py
e.g: test_location_form.py, test_location_model.py, test_location_views.py

====


[![Build Status](https://travis-ci.org/unicefuganda/mics.png?branch=master)](https://travis-ci.org/unicefuganda/mics)
[![Coverage Status](https://coveralls.io/repos/unicefuganda/mics/badge.png)](https://coveralls.io/r/unicefuganda/mics)