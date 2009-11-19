import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader
from opentransit.models import Agency

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
                                       [('ntd_id', lambda x: unicode(x, encoding="utf_8")),
                                        ('name', lambda x: unicode(x, encoding="utf_8")),
                                        ('short_name', lambda x: unicode(x, encoding="utf_8")),
                                        ('city', lambda x: unicode(x, encoding="utf_8")),
                                        ('state', lambda x: unicode(x, encoding="utf_8")),
                                        ('country', lambda x: unicode(x, encoding="utf_8")),
                                        ('agency_url', lambda x: unicode(x, encoding="utf_8") if x!="" else None),
                                        ('address', lambda x: unicode(x, encoding="utf_8")),
                                        ('service_area_population', int),
                                       ])
                                       

loaders = [AgencyLoader]