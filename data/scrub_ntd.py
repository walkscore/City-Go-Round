# further parse the ntdprogram.csv file
import csv
import re

IN_FILENAME = "ntdprogram.csv"
OUT_FILENAME = "agencies.csv"
MERGED_AGENCIES_FILENAME = "merged-agencies.csv"

def main():
    
    long_name_to_external_id = find_long_name_to_external_id( MERGED_AGENCIES_FILENAME )
    
    cr = csv.reader( open( IN_FILENAME ) )
    cw = csv.writer( open( OUT_FILENAME, "w" ) )

    cr.next() # skip header
    cw.writerow( ( "long_name", "short_name", "area", "state", "contact", "email", "url", "phone", "address", "location", "external_id" ) )
    
    for name, location, contact, email, url, phone, address in cr:
        # find long and short name
        matches = re.findall( "(.*)\((.*)\)", name )
        if len(matches)>0:
            long_name = matches[0][0].strip()
            short_name = matches[0][1].strip()
        else:
            long_name = name
            short_name = ""
            
        # replace adddress newline with comma
        address = ", ".join(address.strip().split("\n"))
        
        # if the url contains the substring "file:" make it blank
        if "file://" in url:
            url = None
        
        # find location and state
        loc_area, loc_state = [x.strip() for x in location.split(",")]
        
        #TODO geocode
        location = "0,0"
        
        # get external id
        external_id = long_name_to_external_id.get( name )
        
        cw.writerow( (long_name, short_name, loc_area, loc_state, contact, email, url, phone, address.strip(), location, external_id) )

def find_long_name_to_external_id(filename):
    cr = csv.reader( open( filename ) )
    
    ret = {}
    for line in cr:
        if len(line)==8:
            ret[ line[0] ] = line[7]
    
    return ret

if __name__ == '__main__':
    main()