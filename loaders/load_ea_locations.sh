#!/bin/bash
# This script is used to load administrative divisions CSV into uSurvey container
# Usage (from project directory): ./loaders/load_ea_locations.sh

set -e
set -x

read -p "Enter full path to locations CSV file (see example file administrative_divisions.csv.example): " locations_file

filename=$(basename $locations_file)

cp $locations_file ._docker_mapf

docker-compose run usurvey_app python manage.py import_location "survey/static/map_resources/$filename"

set +x

echo "#####done loading contents. Exiting!"


