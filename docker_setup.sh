#!/usr/bin/env bash

# Basic basic script to boostrap uSurvey setup on linux

if [[ -z "${POSTGRES_DATA_PATH}" ]]; then
    echo "No Volume path set for postgres"
    echo "Setting volume path to /opt/db/data/psql"
    export POSTGRES_DATA_PATH=/opt/data/psql
else
    echo "Using '$POSTGRES_DATA_PATH'"; fi

echo "creating directory $POSTGRES_DATA_PATH is not existing"
sudo mkdir -p $POSTGRES_DATA_PATH

echo '#####                     (33%)'
sleep 1
echo "building project.. Go grab some coffee, it might take a while..."
echo "exec: docker build -t usurvey ."

docker build -t usurvey -f Dockerfile .

echo '#############             (66%)'
sleep 1
echo "Starting app..."
echo ""

export DJANGO_CREATE_SUPER_USER=on
export DJANGO_MANAGEPY_MIGRATE=on

docker-compose -f docker-compose.yml up -d

echo '#######################   (100%)'
echo "Setup Complete!"

echo "To see status of services, Run: docker-compose logs"
echo "Bye!"



