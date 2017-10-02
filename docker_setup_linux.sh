#!/usr/bin/env bash

# Basic basic script to boostrap uSurvey setup on linux

# stop docker if it is currently running
# addresses issue if this file is re-run multiple times
docker-compose down

set -e
#set -x

POSTGRES_DATA_PATH=$1

DEFAULT_PSQL_LOC=/opt/db/data/psql

if [ -z "${POSTGRES_DATA_PATH}" ]; then
    echo "No Volume path set for postgres"
    echo "Setting volume path to $DEFAULT_PSQL_LOC"
    export POSTGRES_DATA_PATH=$DEFAULT_PSQL_LOC
else
    echo "Using '$POSTGRES_DATA_PATH'"; fi

echo "creating directory $POSTGRES_DATA_PATH is not existing"
sudo mkdir -p $POSTGRES_DATA_PATH
sudo chown -R $USER:$USER $POSTGRES_DATA_PATH
chmod +x loaders/*

echo '#####                     '
sleep 1
echo "Starting app..."
echo ""

docker-compose -f docker-compose.yml up -d
echo "Done starting up. "

echo '#############             '
sleep 1
echo "1. Running migrations..."
echo "2. Load Roles and Permissions"
echo "3. create superuser..."
docker-compose run usurvey_app sh -c "python manage.py makemigrations && python manage.py migrate --noinput && \
                                python manage.py load_parameters && python manage.py createsuperuser"
echo "Done creating super user. "

echo '#######################   '
echo "Setup Complete!"

echo "To see status of services, Run: docker-compose logs"
echo "Bye!"



