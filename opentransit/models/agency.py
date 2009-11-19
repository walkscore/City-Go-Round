import logging
from google.appengine.ext import db
from django.core.urlresolvers import reverse
from geo.geomodel import GeoModel
from ..utils.slug import slugify
from ..utils.datastore import key_and_entity, normalize_to_key, normalize_to_keys, unique_entities

class Agency(GeoModel):
    # properties straight out of the NTD import
    ntd_id                = db.StringProperty()
    gtfs_data_exchange_id = db.StringProperty()
    name                  = db.StringProperty(required=True)
    short_name            = db.StringProperty()
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
    phone           = db.StringProperty()
    service_area_population = db.IntegerProperty()
    passenger_miles         = db.IntegerProperty()
    
    # bookkeeping
    updated         = db.DateTimeProperty()
    date_opened     = db.FloatProperty() # not datetime because the FeedReference.date_added is a float
    
    # slugs
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
        
        # set the external_id if it has not already been set
        if self.gtfs_data_exchange_id is None:
            self.gtfs_data_exchange_id = self.nameslug
    
    def to_jsonable(self):
        return {'ntd_id':self.ntd_id,
                'name':self.name,
                'gtfs_data_exchange_id':self.gtfs_data_exchange_id,
                'date_opened':self.date_opened,
                'passenger_miles':self.passenger_miles}
                
    @property
    def is_public(self):
        return (self.date_opened != None)
        
    @staticmethod
    def all_public_agencies():
        """Return a query to all Agency entities marked 'public' by Brandon's import scripts."""
        return Agency.all().filter('date_opened !=', None)
        
    @staticmethod
    def fetch_explicitly_supported_for_transit_app(transit_app):
        """Return a list of Agency entities that are explicitly supported by the transit app."""
        return Agency.get(transit_app.explicitly_supported_agency_keys)
        
    @staticmethod
    def iter_explicitly_supported_for_transit_app(transit_app):
        """Return an iterator over Agency entities that are explicitly supported by the transit app."""
        # Not a true lazy iterator, but this should be plenty fast
        for agency in Agency.fetch_explicitly_supported_for_transit_app(transit_app):
            yield agency
        
    @staticmethod
    def fetch_for_transit_app(transit_app, uniqify = True):
        """Return a list of Agency entities, by default unique, that the given transit app supports"""
        return [agency for agency in Agency.iter_for_transit_app(transit_app, uniqify)]
        
    @staticmethod
    def iter_for_transit_app(transit_app, uniqify = True):
        """Return an iterator over Agency entities, by default unique, that the given transit app supports"""
        seen = {}
        for explicit_agency in Agency.iter_explicitly_supported_for_transit_app(transit_app):
            if (not uniqify) or (explicit_agency.key() not in seen):
                if uniqify: seen[explicit_agency.key()] = True
                yield explicit_agency
        if transit_app.supports_all_public_agencies:
            for public_agency in Agency.all_public_agencies():
                if (not uniqify) or (public_agency.key() not in seen):
                    if uniqify: seen[public_agency.key()] = True
                    yield public_agency
        
    @staticmethod
    def fetch_for_transit_apps(transit_apps, uniqify = True):
        """Return a list of Agency entities, by default unique, that at least one transit application in the transit_apps list supports."""
        return [agency for agency in Agency.iter_for_transit_apps(transit_apps, uniqify)]

    @staticmethod
    def iter_for_transit_apps(transit_apps, uniqify = True):
        """Return an iterator over Agency entities, by default unique, that at least one transit application in the transit_apps list supports."""
        seen = {}
        for transit_app in transit_apps:
            for agency in Agency.iter_for_transit_app(transit_app, uniqify = False):
                if (not uniqify) or (agency.key() not in seen):
                    if uniqify: seen[agency.key()] = True
                    yield agency        
