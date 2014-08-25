#!/bin/sh
cd ..
virtualenv mics_env
source mics_env/bin/activate
cd -
pip install -r pip-requires.txt
pip install coveralls
cp mics/snap-ci/snap-settings.py mics/localsettings.py
./manage.py syncdb --noinput
./manage.py migrate