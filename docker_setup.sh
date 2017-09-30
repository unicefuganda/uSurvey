#!/usr/bin/env bash

# Basic basic script to boostrap uSurvey setup on linux

validate_export () {
    # Usage: validate_export REGEX PROMPT_NAME EXPORT_FIELD
    #  validate input against $1, using prompt name $2, export the result to $3
    value=""
    while :; do
        if [[ ! $value =~ $1 ]]; then
            echo "Expected Input: $1"
            read -p "Enter $2: " value
        else
            break
    fi
    done
    echo "Thanks! Exporting $3=$value"
    export $3=$value
}

#echo "Checking required environment vairables...."
#if [[ -z "${USURVEY_DB}" ]]; then
#    validate_export '^[a-zA-Z][a-zA-Z0-9]+$' 'Database Name' USURVEY_DB
#else
#    echo "Using Database Name: $USURVEY_DB"
#fi
#
#echo ""
#
#if [[ -z "${USURVEY_DB_USER}" ]]; then
#    validate_export '^[a-zA-Z][a-zA-Z0-9]+$' 'Database User' USURVEY_DB_USER
#else
#    echo "Using Database User: $USURVEY_DB_USER"
#fi
#
#echo ""
#
#if [[ -z "${USURVEY_DB_PASS}" ]]; then
#    validate_export '^.+$' 'Database Password' USURVEY_DB_PASS
#else
#    echo "Using Database Password: $USURVEY_DB_PASS"
#fi
#
#echo "..................................................."
#
#if [[ -z "${POSTGRES_DATA_PATH}" ]]; then
#    echo "No Volume path set for postgres"
#    echo "Setting volume path to /opt/db/data/psql"
#    export POSTGRES_DATA_PATH=/opt/data/psql
#else
#    echo "Using '$POSTGRES_DATA_PATH'"; fi

echo "creating directory $POSTGRES_DATA_PATH is not existing"
sudo mkdir -p $POSTGRES_DATA_PATH

echo "..................................................."

echo "building project.. Go grab some coffee, it might take a while..."
echo "exec: docker build -t usurvey ."

docker build -t usurvey -f Dockerfile .

DATABASE_URL=none python manage.py collectstatic --noinput

echo "..................................................."

echo ""
echo "Starting app..."
echo ""

export DJANGO_CREATE_SUPER_USER=on
export DJANGO_MANAGEPY_MIGRATE=on

docker-compose -f docker-compose.yml up -d

echo "..................................................."
echo "Setup Complete!"

echo "To see status of services, Run: docker-compose logs"
echo "Bye!"



