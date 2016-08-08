Usurvey Support Guide
=====================

##Fresh Setup

###Initial Load data
For fresh installation, following two commands should be ran to load initial data. 
 
One is for initial location data, the other is for the custom permissions and other system data 

- To load location data run the following command
    
    > python manage.py import_location [LOCATION_FILE_CSV]
    
    The first line of the csv file shall be taken as file header. 
    
    The file header is expected to contain names as per the Administrative division of the current country in a comma separated format. The last entry of the header can contain EAName  
    Eg. For Uganda, example headers can be **Country,DistrictName,CountyName,SubCountyName,ParishName,VillageName,EAName** 
    
    Eg. For Nigeria, example headers can be **Country,State,Local Government Area,EAName** 
    
    The file header is used to create Administrative structure within the system. Subsequent lines of the file used to create locations data associated with the Administrative area.
    
    * Tab to create futher Administrative Areas has been disabled from UI. This is to be part of Initial setup
    * More locations can be loaded by running the above script
    * To create/Modify Enumeration areas, use the Enumeration Area Tab on UI
     
- To load other system data run the following command
 
    > python manage.py load_parameters
    
  This loads the custom permission and configurations for ODK and USSD access
  
### Setting up Shape file

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
       
####Note: 
uSurvey expects shape file for the primary Administrative divisions of a country. 
Eg. If for Nigeria, system configuration for Administrative structure is  **Country,State,Local Government Area,EAName**,  Shape file should capture shapes for State only. Since uSurvey captures map reports based on the Primary Administrative division of the country.
For Uganda, shape file would be based on Districts likewise. 
    
    



