mics
====

Installation
------------
* Postgres, redis-server should be running

* It helps to install python-dev, libxml2-dev, libxslt1-dev, zlib1g-dev and libffi-dev (for a debian based system, the command would be *sudo apt-get install python-dev libxml2-dev libxslt1-dev zlib1g-dev libffi-dev*)

* Execute the following commands from your installation directory:

        git clone https://github.com/unicefuganda/uSurvey.git

        cd uSurvey/mics

        cp travis-settings.py localsettings.py
        (adjust localsettings.py for db and test_db setup)

        cd ../survey

        cp interviewer_configs.py.example interviewer_configs.py

        cd ..

        mkvirtualenv uSurvey

        pip install -U -r pip-requires.txt

        python manage.py syncdb --noinput

        python manage.py makemigrations
        
        python manage.py migrate

        python manage.py createsuperuser
        (to create the initial user access)

        python manage.py load_parameters

Before using the system
-----------------------
       
* Before using the setup, you need to load data for administrative divisions of the required country.

* To load administrative divisions into the system, run the following commands:

        python manage.py import_location [LOCATION_FILE_CSV]

> The first line of the csv file shall be taken as file header. 

> The file header is expected to contain names as per the administrative division in a comma separated format. In addition, there can be an additional header for enumeration area. This header should be named *EAName*. Sample file for Uganda is included in the project directory as administrative_divisions.csv.example.


Starting up
-----------

* Make sure you configure appropriate ports in the supervisord.conf file.

* Start the system using supervisor:

        supervisord -c supervisord.conf

> In supervisord.conf, the configuration under [program:odk-server] is required to serve ODK requests, while the configuration under [program:django-interface-server] is for serving other requests.


==

Testing
-------

* run test as follows:

        python manage.py test


====

[![Build Status](https://travis-ci.org/unicefuganda/uSurvey.svg)](https://travis-ci.org/unicefuganda/uSurvey)
