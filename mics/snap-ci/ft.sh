#!/bin/sh
source ../mics_env/bin/activate
cp mics/snap-ci/snap-settings.py mics/localsettings.py
./manage.py harvest
