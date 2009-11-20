import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader
from opentransit.models import Agency

#note - you will need to modify your $PYTHONPATH 
# to include both opentransit and opentransit/opentransit:
# $ export PYTHONPATH=/path/to/opentransitdata:path/to/opentransitdata/opentransit
# $ /home/brandon/downloads/google_appengine/appcfg.py upload_data . --filename=./data/agencies.csv --kind=Agency --config_file=./data/agency_loader.py --url=http://localhost:8080/remote_api --has_header

def smart_utf8(x):
    return unicode(x, encoding="utf_8") if x!="" else None
        
def smart_list(x):
    return [unicode(x, encoding="utf_8")] if x!="" else []
        
def smart_int(x):
    return int(x) if x!="" else None

class AgencyLoader(bulkloader.Loader):
    def __init__(self):
    
        def lat_lon(s):
            lat, lon = [float(v) for v in s.split(',')]
            return db.GeoPt(lat, lon)
        
        bulkloader.Loader.__init__(self, 'Agency',
                                       [('ntd_id', smart_utf8),
                                        ('name', smart_utf8),
                                        ('short_name', smart_utf8),
                                        ('city', smart_utf8),
                                        ('state', smart_utf8),
                                        ('country', smart_utf8),
                                        ('agency_url', smart_utf8),
                                        ('address', smart_utf8),
                                        ('service_area_population', smart_int),
                                        ('passenger_miles', smart_int),
                                        ('gtfs_data_exchange_id', smart_list),
                                        ('executive', smart_utf8),
                                        ('executive_email', smart_utf8),
                                        ('location',str),
                                       ])
                                       

loaders = [AgencyLoader]