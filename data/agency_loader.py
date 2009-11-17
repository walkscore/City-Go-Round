import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader
from ..utils.slug import slugify

class AgencyLoader(bulkloader.Loader):
    def __init__(self):
    
    def lat_lon(s):
        lat, lon = [float(v) for v in s.split(',')]
        return db.GeoPt(lat, lon)
    
        bulkloader.Loader.__init__(self, 'Agency',
                                   [('long_name', str),
                                    ('short_name', str),
                                    ('area', str),
                                    ('state', str),
                                    ('contact', str),
                                    ('url', str),
                                    ('phone', str),
                                    ('address', str),
                                    ('location', lat_lon)
                                   ])
                                   
                                   
    def handle_entity(self, entity):
        entity.update_location()
        entity.urlslug = '/'.join(map(slugify,[entity.state, entity.city, entity.name)])
        return entity

loaders = [AgencyLoader]