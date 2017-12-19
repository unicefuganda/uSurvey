uSurvey
=======
[![Build Status](https://travis-ci.org/unicefuganda/uSurvey.svg?branch=uSurvey)](https://travis-ci.org/unicefuganda/uSurvey)
[![Coverage Status](https://coveralls.io/repos/github/unicefuganda/uSurvey/badge.svg?branch=uSurvey)](https://coveralls.io/github/unicefuganda/uSurvey?branch=uSurvey)

uSurvey is an innovative data collection tool designed to provide statistically representative real time estimates of a given indicator. It runs on USSD (Unstructured Supplementary Service Data) interactive secured channel and on ODK (Open Data Kit), for off-line data collection in locations with intermittent mobile network connections.

The system has been designed to collect a wide range of data for the structured survey; to generate and produce descriptive statistics and graphical representation of the collected information whenever desired, as well as during the process of data collection.

Official documentation is available on [http://usurvey.readthedocs.io/](http://usurvey.readthedocs.io/).


Quick Start
-----------

The easiest way to be up and running with uSurvey is to use the docker setup.


* Clone the uSurvey Application from Github 

        git clone https://github.com/unicefuganda/uSurvey.git


* Enter the project directory 

        cd uSurvey

* Update the database entries in ``.env`` file found in the project directory
        
* Run the following commands in the project directory:

        chmod +x docker_setup_linux.sh

        ./docker_setup_linux.sh
        

    **This step performs the following activities:**
        1. Creates path where database files are stored on host machine
        2. Loads the necessary Permissions categories.
        3. Creates a super user to enable you login to uSurvey (requires you to supply login credentials)
        4. Attempts to setup up the map for your country

* Once done, enter the following address on your browser to be sure uSurvey is properly setup:
    
    
    http://localhost:8071/
    
    
What next
---------

You would need to load the administrative divisions data for the country you have made your setup for.
    
See the uSurvey documentation for further information:

[http://usurvey.readthedocs.io/](http://usurvey.readthedocs.io/)


Testing
-------

* run test as follows:

    python manage.py test

