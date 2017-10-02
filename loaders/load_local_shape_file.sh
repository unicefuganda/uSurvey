#!/usr/bin/env bash

set -e
#set -x

read -p "Enter full path to Map shape file: " shape_file

filename=$(basename $shape_file)

echo "#####executing command docker cp $shape_file $(docker ps --format "{{.Names}}" \
      | grep usurvey_app):/src/static/map_resources/"

docker cp $shape_file $(docker ps --format "{{.Names}}" | grep usurvey_app):/src/static/map_resources/

echo "#####copied $filename into container. loading contents..."

echo "#####done loading contents. Exiting!"