Testing
=======

uSurvey uses [Travis CI](https://travis-ci.org/unicefuganda/uSurvey "CI") for continuous integration when ever code is pushed to the [repo](https://github.com/unicefuganda/uSurvey/ "github repo").


Travis builds are a pass only when the the project builds without errors and all test cases are successful.


* However, to manually run tests, execute the following commands:

        python manage.py test


* You can also run the tests with coverage to confirm the coverage reports
        
        coverage run manage.py test
        coverage report


[![Build Status](https://travis-ci.org/unicefuganda/uSurvey.svg)](https://travis-ci.org/unicefuganda/uSurvey)