# further parse the ntdprogram.csv file
import csv
import re

IN_FILENAME = "ntdprogram.csv"
OUT_FILENAME = "agencies.csv"

if __name__ == '__main__':
    cr = csv.reader( open( IN_FILENAME ) )
    cw = csv.writer( open( OUT_FILENAME, "w" ) )

    cr.next() # skip header
    cw.writerow( ( "long_name", "short_name", "area", "state", "contact", "email", "url", "phone", "address", "location" ) )
    
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
        
        
        cw.writerow( (long_name, short_name, loc_area, loc_state, contact, email, url, phone, address.strip()), location )