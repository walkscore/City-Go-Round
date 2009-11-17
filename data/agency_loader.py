import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader
from models import Agency

#note - you will need to modify your $PYTHONPATH 
# to include both opentransit and opentransit/opentransit:
# $ export PYTHONPATH=/path/to/opentransitdata:path/to/opentransitdata/opentransit
# $ /home/brandon/downloads/google_appengine/appcfg.py upload_data . --filename=./data/agencies.csv --kind=Agency --config_file=./data/agency_loader.py --url=http://localhost:8080/remote_api --has_header

class AgencyLoader(bulkloader.Loader):
    def __init__(self):
    
        def lat_lon(s):
            lat, lon = [float(v) for v in s.split(',')]
            return db.GeoPt(lat, lon)
        
        bulkloader.Loader.__init__(self, 'Agency',
                                       [('name', str),
                                        ('short_name', str),
                                        ('city', str),
                                        ('state', str),
                                        ('executive', str),
                                        ('executive_email', str),
                                        ('agency_url', lambda x: str(x) if x!="" else None),
                                        ('phone', str),
                                        ('address', str),
                                        ('location', lat_lon)
                                       ])
                                       

loaders = [AgencyLoader]