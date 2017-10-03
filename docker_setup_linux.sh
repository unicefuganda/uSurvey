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



# expected that docker must have created the file _docker_mapf
sudo chown -R $USER:$USER ._docker_mapf
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
printf "${RED}Attempting map setup.${NC}\n"
printf "${RED}Note:${NC} ${YELLOW}If this step fails, either re-run this setup script or resolve the map's \
shape file manually${NC}\n"
printf "${YELLOW}To setup the map manually, see map section on  \
https://usurvey.readthedocs.io/en/latest/docker_installation/ ${NC}\n"

read -p "Enter country name in full (e.g Uganda or United States of America): " country_name
# country name to lower case
country_name=$(echo "$country_name" | tr '[:upper:]' '[:lower:]')
# replace space with hyphen
country_name=$(echo $country_name | sed -e 's, ,-,g')
MAP_URL_BASE=https://s3.amazonaws.com/osm-polygons.mapzen.com
country_filename="${country_name}_geojson.tgz"
country_url="${MAP_URL_BASE}/${country_filename}"
set -x
tmp_dir=$(mktemp -d "/tmp/usurvey-${country_name}.XXXXX")
wget -P $tmp_dir $country_url
tar -xzf "$tmp_dir/${country_name}_geojson.tgz"  --directory $tmp_dir
set +x
echo "trying out admin level first guess"
set -x
geojson_file="${tmp_dir}/${country_name}/admin_level_4.geojson"
feature_count=$(python -c "import json;print len(json.loads(open('$geojson_file').read()).get('features', []))")
if [ "$feature_count" = "0" ];
    then
        set +x
        echo "trying out admin level second guess"
        set -x
        geojson_file="${tmp_dir}/${country_name}/admin_level_3.geojson"
        feature_count=$(python -c "import json;print len(json.loads(open('$geojson_file').read()).get('features', []))")
fi
#if after everything no show, exit
if [ "$feature_count" != "0" ];
    then
        echo "Found map file: $geojson_file."
        echo "coping $geojson_file..."
        cp $geojson_file ._docker_mapf/country_shape_file.json
        echo "Also keeping a copy in _docker_mapf/"
        cp $geojson_file ._docker_mapf/
else
    echo "Map file not found. Please resolve manually"
    cp survey/static/map_resources/country_shape_file.json ._docker_mapf/
fi

#cleaning up
rm -rf $tmp_dir
set +x

#

echo '#######################   '
echo "Setup Complete!"

echo "To see status of services, Run: docker-compose logs"
echo "Bye!"



