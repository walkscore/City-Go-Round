import csv

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

IN_FILENAME = "ntd_agencies.csv"
SERVICE_LEVEL_FILENAME = "service.csv"
OUT_FILENAME = "agencies.csv"

service_level = get_service_level( SERVICE_LEVEL_FILENAME )

cr = csv.reader( open( IN_FILENAME ) )
cw = csv.writer( open( OUT_FILENAME, "w" ) )

header = cr.next()
headerindex = dict( zip( header, range(len(header)) ) )

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
    
    cw.writerow( (ntd_id, name, short_name, city, state, country, agency_url, address, service_area_population, agency_service_level) )