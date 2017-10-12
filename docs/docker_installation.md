Docker Setup (Linux)
===================

* This section covers uSurvey installation from docker image. 
* For uSurvey installation from source, [check here](./installation.md)


Prerequisites
------------- 

* Linux Machine (Preferably Ubuntu 12+)

* Minimum of 2GB RAM for test environment 

* 16GB RAM should be enough for production setups with less than 1 million survey submissions per day on a 2GHz clock speed machine.

* Docker must be installed. You can find details for your Linux [here](https://docs.docker.com/engine/installation/)


Quick Start
-----------

* Clone the uSurvey Application from Github 

        git clone https://github.com/unicefuganda/uSurvey.git -b dev


* Enter the project directory 

        cd uSurvey

* Update the database entries in ``.env`` file in the project directory
        
* Run the setup script in the project directory and follow the instructions

        chmod +x docker_setup_linux.sh

        ./docker_setup_linux.sh
        

    * This step performs the following activities:
        1. Creates path where database files are stored on host machine
        2. Loads the necessary Permissions categories.
        3. Creates a super user to enable you login to uSurvey (requires you to supply login credentials)
        4. Attempts to setup up the map for your country

* Once done, enter the following address on your browser to be sure uSurvey is properly setup:
    
    
    http://localhost:8071/



Customizing the country data
----------------------------
       
###Loading Location Data
       
* Before using the setup, you need to load data for administrative divisions of the required country.

    * A sample of the required CSV file is available in the project directory ([administrative_divisions.csv.example](./administrative_divisions.csv.example) for Uganda and [administrative_divisions_india.csv.example](./administrative_divisions_india.csv.example) for India)

* To load administrative divisions into the system, run the following commands from the project directory and follow the steps:    


    sh ./loaders/load_ea_locations.sh

####Note
**The first line of the csv file shall be taken as file header.** 

**The file header is expected to contain names as per the administrative division in a comma separated format. In addition, there can be an additional header for enumeration area. This header should be named *EAName*. Sample file for Uganda is included in the project directory as [administrative_divisions.csv.example](./administrative_divisions.csv.example).**


###Setting Up Map Reporting

**If you plan to use uSurvey in Uganda, then this step is not required!**

**The recommended way to setup the map on linux is using the docker_setup_linux.sh script. However if that fails, the following steps explains how map setup can be done manually**

To enable uSurvey capture survey data in a specific country's map, you need to update the map settings section within the ``.env`` file. This file is available in the project directory.

This is required because uSurvey must be made aware of the shape file to use. 

The the map settings section holds sufficient documentation on the purpose of each settings field.

The expected GeoJson files should be compatible with specification at [http://geojson.org/geojson-spec.html](http://geojson.org/geojson-spec.html)

The GeoJson file for your country most likely can be downloaded from [https://mapzen.com/data/borders/](https://mapzen.com/data/borders/).

Several shape files are presented there for each download so be sure to select the file which captures the administrative level map which you are interested in.


Starting Up
-----------

* **By default uSurvey is set to run on 8071, however you can change this in the .env file**
* **You can have uSurvey sit behind a reverse proxy server like nginx also.**
* **With current the docker setup, you can scale up just as easily as with any docker containers.**

####Note:
    * If you have started uSurvey with the docker_setup_linux.sh, then uSurvey must already be up and running.

* To startup using docker-compose, run the command below:

         docker-compose up -d
        
* To stop uSurvey using docker-compose, run the command below:
        
        docker-compose down
