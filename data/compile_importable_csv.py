import csv
try:
    import simplejson as json
except ImportError:
    import json
import re
from geocoder import geocode_name
import time

"""
    'ntd_id': 'Trs_Id',
    'name':'Company_Nm',
    'short_name':'Logo_Cd',
    'city':'City_Nm',
    'state':'State_Desc',
    'country':'us',
    'postal_code' Zip_Cd-Zip_4_Cd
    'address', Street1_Nm + Street2_Nm, City_Nm, State_Desc Zip_Cd-Zip_4_Cd
    'agency_url' Url_Cd
    'service_area_population': Service_Area_Population
"""

def parse_comma_int(str):
    if str=="":
        return None
    
    return int("".join(str.split(",")))
    
def get_service_level( filename ):
    """use service level file to find dict of ntdid:passenger_miles"""
    
    cr = csv.reader( open( filename ) )

    sums = {}

    header = cr.next()
    headerindex = dict( zip( header, range(len(header)) ) )

    print header

    for row in cr:
        ntd_id = row[ headerindex["Trs_Id"] ].strip()
        
        if ntd_id not in sums:
            sums[ntd_id] = 0
            
        time_period_desc = row[ headerindex["Time_Period_Desc"] ].strip()
        
        if time_period_desc == "Annual Total":
            passenger_miles = parse_comma_int(row[ headerindex["Passenger_Miles"] ].strip())
            
            if passenger_miles is not None:
                sums[ntd_id] += passenger_miles
            
    return sums
    
def get_gtfs_data_exchange_ids( gtfs_data_exchange_id_filename ):
    """use agency database snapshot to find dict of ntdid:gtfs_data_exchange_id"""
    
    NTDID_COL = 0
    GTFSDEID_COL = 3
    
    cr = csv.reader( open( gtfs_data_exchange_id_filename ) )
    
    ret = dict( [ (row[NTDID_COL], row[GTFSDEID_COL]) for row in cr ] )
    
    return ret
    
def get_contact_information( scraped_filename ):
    """ use jehiah's screenscrape file to find dict of agency_name:contact_information """
    
    NAME_COL = 0
    CONTACT_COL = 2
    EMAIL_COL = 3
    
    cr = csv.reader( open( scraped_filename ) )
    
    ret = dict( [ (name_to_base_name(row[NAME_COL]), {'name':row[CONTACT_COL], 'email':row[EMAIL_COL]}) for row in cr ] )
    
    return ret
    
def name_to_base_name(name):
    """cuts out basename in string like "Transit Authority (TA)"""
    
    matches = re.findall( "(.*)\((.*)\)", name )
    if len(matches)>0:
        base_name = matches[0][0].strip()
        short_name = matches[0][1].strip()
    else:
        base_name = name
        short_name = ""
        
    return base_name

IN_FILENAME = "ntd_agencies.csv"
SERVICE_LEVEL_FILENAME = "service.csv"
OUT_FILENAME = "agencies.csv"
GTFS_IDS_FILENAME = "gtfs_data_exchange_ids.csv"
SCREENSCRAPE_FILENAME = "ntdprogram.csv"
API_KEY = "ABQIAAAARFBfEeey0ac5JKru_9nB4BRNy0I-ty1ceBzDzdazMPQQJBF-YBTicqpsbJEKspGxit8ea-iSAtSD9A"
DELAY = 3

service_level = get_service_level( SERVICE_LEVEL_FILENAME )
data_exchange_ids = get_gtfs_data_exchange_ids( GTFS_IDS_FILENAME )
contact_information = get_contact_information( SCREENSCRAPE_FILENAME )

cr = csv.reader( open( IN_FILENAME ) )
cw = csv.writer( open( OUT_FILENAME, "w" ) )

header = cr.next()
headerindex = dict( zip( header, range(len(header)) ) )

cw.writerow( ('ntd_id', 'name', 'short_name', 'city', 'state', 'country', 'agency_url', 'address', 'service_area_population', 'agency_service_level', 'gtfs_data_exchange_id', 'contact_name', 'contact_email', 'location') ) 

for row in cr:
    ntd_id = row[ headerindex["Trs_Id"] ].strip()
    name = row[ headerindex["Company_Nm"] ].strip()
    short_name = row[ headerindex["Logo_Cd"] ].strip()
    city = row[ headerindex["City_Nm"] ].strip()
    state = row[ headerindex["State_Desc"] ].strip()
    country = "us"
    
    # postal code
    postal_code = row[ headerindex["Zip_Cd"] ].strip()
    if row[ headerindex["Zip_4_Cd"] ].strip() != "":
        postal_code = postal_code + "-" + row[ headerindex["Zip_4_Cd"] ].strip()
    
    # address
    streetaddress = row[ headerindex["Street1_Nm"] ].strip()
    if row[ headerindex["Street2_Nm"] ].strip() != "":
        streetaddress = streetaddress + "-" + row[ headerindex["Street2_Nm"] ].strip()
    address = "%s, %s, %s, %s"%(streetaddress, city, state, postal_code)
    
    # url
    agency_url = row[ headerindex["Url_Cd"] ].strip()
    if agency_url != "" and agency_url[:7] != "http://":
        agency_url = "http://"+agency_url
    
    service_area_population = parse_comma_int(row[ headerindex["Service_Area_Population"] ].strip())
    
    agency_service_level = service_level.get(ntd_id)
    
    gtfs_data_exchange_id = data_exchange_ids.get(ntd_id)
    
    contact_info = contact_information.get( name, {} )
    
    coords = geocode_name( city, state, API_KEY )
    location = str(coords[1]) + ',' + str(coords[0])
    
    cw.writerow( (ntd_id, name, short_name, city, state, country, agency_url, address, service_area_population, agency_service_level, gtfs_data_exchange_id, contact_info.get('name'), contact_info.get('email'), location) )
    
    time.sleep(0.5)