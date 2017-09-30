#!/bin/sh
set -e

until psql $DATABASE_URL -c '\l'; do
  >&2 echo "Postgres: $DATABASE_URL is unavailable - sleeping"
  sleep 1
done

 >&2 echo "Postgres is up - continuing"

 >&2 echo "checking migration settings: $DJANGO_MANAGEPY_MIGRATE"

if [ "x$DJANGO_MANAGEPY_MIGRATE" = 'xon' ]; then
>&2 echo "Running migrations. "
    python manage.py makemigrations
    python manage.py migrate --noinput
fi

if [ "x$DJANGO_CREATE_SUPER_USER" = 'xon' ]; then
>&2 echo "creating superuser..."
    python manage.py createsuperuser
fi

exec "$@"

