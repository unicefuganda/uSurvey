

Prerequisites
------------- 

* Has been tested on Ubuntu and OS X. However it should run on most Linux machines (since there are no distribution specific dependency).

* Minimum of 1GB RAM is recommended for setup.

* Postgres, redis-server should be running

* It helps to install python-dev, libxml2-dev, libxslt1-dev, zlib1g-dev and libffi-dev (for a debian based system, the command would be *sudo apt-get install python-dev libxml2-dev libxslt1-dev zlib1g-dev libffi-dev*)

* uSurvey has been tested on python2.7 and is compatible with django 1.8 and django 1.9 as of this time of writing. 

* Required python libraries are contained in the pip-requires.txt file found within the project directory.


Installation Instructions
-------------------------

* Clone the uSurvey Application from Github 

        git clone https://github.com/unicefuganda/uSurvey.git

* Go to mics folder in uSurvey 

        cd uSurvey/mics

* Copy customized settings in localsettings.py 

        cp travis-settings.py localsettings.py
        (adjust localsettings.py for db and test_db setup)
        
* Go to survey folder in uSurvey

        cd ../survey

* Copy config file interviewer_configs.py

        cp interviewer_configs.py.example interviewer_configs.py

        cd ..

        mkvirtualenv uSurvey

        pip install -U -r pip-requires.txt

        python manage.py syncdb --noinput

        python manage.py makemigrations
        
        python manage.py migrate

        python manage.py createsuperuser
        (to create the initial user access)

        python manage.py load_parameters


Before Using The System
-----------------------
       
###Loading Location Data
      
* Before using the setup, you need to load data for administrative divisions of the required country.

* To load administrative divisions into the system, run the following commands:

        python manage.py import_location [LOCATION_FILE_CSV]

> The first line of the csv file shall be taken as file header. 

> The file header is expected to contain names as per the administrative division in a comma separated format. In addition, there can be an additional header for enumeration area. This header should be named *EAName*. Sample file for Uganda is included in the project directory as administrative_divisions.csv.example.

###Setting Up Map Reporting

To enable uSurvey capture survey data in country map, A few settings needs to be made on the ``mics/settings.py`` file.

uSurvey must be made aware of the shape file to use. The shape file is expected to contain json data. 

Sample data is given below:  
``` 
{
"type": "FeatureCollection",
"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },                                                                               
"features": [
{ "type": "Feature", "properties": { "D_06_ID": 1.0, "DNAME_2006": "KALANGALA", "AREA": 7745049286.718000411987305, "PERIMETER": 360086.68, "HECTARES": 774504.929, "SUBREGION": "CENTRAL 1", "UNICEF": "Kampala Office", "Reg_2011": "BUGANDA" }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 32.752554625197888, -0.149071180159047 ], [ 32.750256065472698, -0.997321195816234 ], [ 31.999165348402585, -0.997177585925673 ], [ 31.999929505377516, -0.382633576354547 ], [ 32.051271530088805, -0.335753704721339 ], [ 32.060643971387883, -0.303713379631932 ], [ 32.052504995368089, -0.272422328207899 ], [ 31.999540508585685, -0.216387568658223 ], [ 31.999689880245036, -0.151003632585263 ], [ 32.752554625197888, -0.149071180159047 ] ] ] } },
{ "type": "Feature", "properties": { "D_06_ID": 1.0, "DNAME_2006": "KAMPALA", "AREA": 194305275.828, "PERIMETER": 68787.571, "HECTARES": 19430.528, "DNAME_2010": "KAMPALA", "SUBREGION": "CENTRAL 1", "UNICEF": "Kampala Office", "Reg_2011": "BUGANDA" }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 32.662105969306658, 0.284035417622536 ], [ 32.668022498091105, 0.277322598528355 ], [ 32.642901670945534, 0.245503088979917 ], [ 32.633514160694709, 0.217049622340069 ], [ 32.61518676687917, 0.229045627821064 ], [ 32.602891067137875, 0.259579229993582 ], [ 32.576991771882362, 0.280838983682295 ], [ 32.540136902642004, 0.27453181081871 ], [ 32.525943524305809, 0.300921350829158 ], [ 32.511397956843844, 0.30698218131173 ], [ 32.528979095921613, 0.342094394182897 ], [ 32.552912274710792, 0.351196862084601 ], [ 32.549160409492757, 0.378292529722675 ], [ 32.563782266921734, 0.389728747789749 ], [ 32.561716231138071, 0.40457483717538 ], [ 32.602177690381076, 0.407951500236093 ], [ 32.604336893211176, 0.393440071681235 ], [ 32.616880284253924, 0.390446068960009 ], [ 32.618548630962067, 0.380069112734243 ], [ 32.633974927458965, 0.380639753518482 ], [ 32.642330629075914, 0.330129964364422 ], [ 32.664678497107538, 0.32662949942806 ], [ 32.662105969306658, 0.284035417622536 ] ] ] } },
]}
```

Required settings are given below:

- SHAPE_FILE_URI: This is the URI pointing to the shape file of the country. Example configurations are
    
    > SHAPE_FILE_URI = '/static/map_resources/uganda_districts_2011_005.json'
    
    > SHAPE_FILE_URI = 'http://someothershapedata/resources/mycountry.json'

- SHAPE_FILE_LOC_FIELD: This is the primary field used to indicate the corresponding Administrative area whose shape file is presented in shape file list item.
    
- SHAPE_FILE_LOC_ALT_FIELD: This is the secondary field used to indicate the corresponding Administrative area whose shape file is presented in shape file list item. This entry shall be used if **SHAPE_FILE_LOC_FIELD** is missing in any shape data list item


Starting Up
-----------

* **Make sure you configure appropriate ports in the supervisord.conf file.**

* Start the system using supervisor:

        supervisord -c supervisord.conf

> In supervisord.conf, the configuration under [program:odk-server] is required to serve ODK requests, while the configuration under [program:django-interface-server] is for serving other requests.
> Only the ports configured in [program:odk-server] and [program:django-interface-server] are required to handle requests. Other ports configured on supervisord.conf file are for managing supervisor
