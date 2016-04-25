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

        pip install -U -r pip-requires.txt

        python manage.py syncdb --noinput

        python manage.py makemigrations
        
        python manage.py migrate

        python manage.py load_parameters

        python manage.py runserver

==

* run test

        python manage.py test


====


[![Build Status](https://travis-ci.org/antsmc2/mics.svg?branch=uSurvey)](https://travis-ci.org/unicefuganda/mics)
[![Coverage Status](https://coveralls.io/repos/unicefuganda/mics/badge.png)](https://coveralls.io/r/unicefuganda/mics)