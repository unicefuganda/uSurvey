#!/usr/bin/env bash

set -e
#set -x

read -p "Enter full path to locations CSV file (see example file administrative_divisions.csv.example): " locations_file

filename=$(basename $locations_file)

echo "#####executing command docker cp $locations_file $(docker ps --format "{{.Names}}" | grep usurvey_app):/src/"

docker cp $locations_file $(docker ps --format "{{.Names}}" | grep usurvey_app):/src/

echo "#####copied $filename into container. loading contents..."

docker-compose run usurvey_app python manage.py import_location $filename

echo "#####done loading contents. Exiting!"


