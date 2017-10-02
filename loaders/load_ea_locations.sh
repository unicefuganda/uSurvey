#!/bin/bash
# This script is used to load administrative divisions CSV into uSurvey container
# Usage (from project directory): ./bin/load_ea_locations.sh

set -e
set -x

read -p "Enter full path to locations CSV file (see example file administrative_divisions.csv.example): " locations_file

filename=$(basename $locations_file)

docker cp $locations_file $(docker ps --format "{{.Names}}" | grep usurvey_app):/src/

docker-compose run usurvey_app python manage.py import_location $filename

set +x

echo "#####done loading contents. Exiting!"


