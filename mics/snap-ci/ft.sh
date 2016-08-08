#!/bin/sh
source ../mics_env/bin/activate
cp mics/snap-ci/snap-settings.py mics/localsettings.py
cp survey/investigator_configs.py.example survey/investigator_configs.py
./manage.py harvest
