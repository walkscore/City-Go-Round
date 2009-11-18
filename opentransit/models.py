import logging
from google.appengine.ext import db
from django.core.urlresolvers import reverse
from geo.geomodel import GeoModel
from utils.slug import slugify

class PetitionModel(db.Model):
    name        = db.StringProperty()
    email       = db.EmailProperty()
    city        = db.StringProperty()
    state       = db.StringProperty()
    country     = db.StringProperty()
    
class Agency(GeoModel):
    external_id     = db.StringProperty()
    name            = db.StringProperty(required=True)
    short_name      = db.StringProperty()
    tier            = db.IntegerProperty()
    city            = db.StringProperty(required=True)
    state           = db.StringProperty(required=True)
    country         = db.StringProperty(default="us")
    postal_code     = db.IntegerProperty()
    address         = db.StringProperty()
    agency_url      = db.LinkProperty()
    executive       = db.StringProperty()
    executive_email = db.EmailProperty()
    twitter         = db.StringProperty()
    contact_email   = db.EmailProperty()
    updated         = db.DateTimeProperty()
    phone           = db.StringProperty()
    
    nameslug        = db.StringProperty()
    cityslug        = db.StringProperty()
    stateslug       = db.StringProperty()
    countryslug     = db.StringProperty()
    urlslug         = db.StringProperty()
    
    def __init__(self, *args, **kwargs):
        # this loads everything to self that's passed as a kwarg, making required and default attribs safe to use
        GeoModel.__init__(self, *args, **kwargs)
        
        self.nameslug = slugify(self.name)
        self.cityslug = slugify(self.city)
        self.stateslug = slugify(self.state)
        self.countryslug = slugify(self.country)
        self.urlslug = "%s/%s/%s/%s"%(self.countryslug,self.stateslug,self.cityslug,self.nameslug)
    
class FeedReference(db.Model):
    """feed reference models a GTFS Data Exchange entity"""
    
    external_id       = db.StringProperty()
    date_last_updated = db.FloatProperty()
    feed_baseurl      = db.LinkProperty()
    name              = db.StringProperty()
    area              = db.StringProperty()
    url               = db.LinkProperty()
    country           = db.StringProperty()
    dataexchange_url  = db.LinkProperty()
    state             = db.StringProperty()
    license_url       = db.LinkProperty()
    date_added        = db.FloatProperty()
    is_official       = db.BooleanProperty(default=True)
    
    @staticmethod
    def all_by_most_recent():
        return FeedReference.all().order("-date_added")
    
class TransitAppStats(db.Model):
    # low contention model -- don't bother with sharding
    transit_app_count   = db.IntegerProperty()
    
    @staticmethod
    def get_transit_app_stats():
        # A "singleton" datastore entry for now
        stats = TransitAppStats.all().get()
        if stats is None:
            stats = TransitAppStats(transit_app_count = 0)
            try:
                stats.put()
            except db.TimeoutException:
                stats.put()
        return stats
            
    @staticmethod
    def get_transit_app_count():
        return TransitAppStats.get_transit_app_stats().transit_app_count
        
    @staticmethod
    def increment_transit_app_count():
        stats = TransitAppStats.get_transit_app_stats()
        stats.transit_app_count = stats.transit_app_count + 1
        try:
            stats.put()
        except db.TimeoutException:
            stats.put()
    
class TransitApp(db.Model):
    slug                = db.StringProperty(indexed=True)
    title               = db.StringProperty()
    description         = db.StringProperty()
    url                 = db.LinkProperty()
    author_name         = db.StringProperty()
    author_email        = db.EmailProperty()
    long_description    = db.TextProperty()
    tags                = db.StringListProperty()
    screen_shot         = db.BlobProperty()
    
    @property
    def has_screen_shot(self):
        return (self.screen_shot is not None)
        
    @property
    def screen_shot_url(self):
        if self.has_screen_shot:
            return reverse('apps_screenshot', kwargs = {'transit_app_slug': self.slug})
        else:
            return "/images/default-transit-app.png"            
        
    @staticmethod
    def transit_app_for_slug(transit_app_slug):
        return TransitApp.all().filter('slug =', transit_app_slug).get()
    
    @staticmethod
    def has_transit_app_for_slug(transit_app_slug):
        return (TransitApp.transit_app_for_slug(transit_app_slug) is not None)
