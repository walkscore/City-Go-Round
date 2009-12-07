import logging
from google.appengine.ext import db
from google.appengine.api import memcache
from django.conf import settings
from django.core.urlresolvers import reverse
from geo.geomodel import GeoModel
from ..utils.slug import slugify
from ..utils.datastore import key_and_entity, normalize_to_key, normalize_to_keys, unique_entities, iter_uniquify
from ..utils.geohelpers import square_bounding_box_centered_at
from ..utils.misc import uniquify
import cgi

class Agency(GeoModel):
    # properties straight out of the NTD import
    ntd_id                = db.StringProperty()
    gtfs_data_exchange_id = db.ListProperty(unicode)
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
    date_opened     = db.DateTimeProperty()
    
    # developer amenities
    dev_site         = db.LinkProperty() #None if no developer site
    arrival_data     = db.LinkProperty() #Link to arrival data source; None if no arrival data
    position_data    = db.LinkProperty() #Link to position data source; None if no position data
    standard_license = db.StringProperty() #String of standard license like "GPL"; None if no standard license    
    
    # slugs
    nameslug        = db.StringProperty()
    cityslug        = db.StringProperty()
    stateslug       = db.StringProperty()
    countryslug     = db.StringProperty()
    urlslug         = db.StringProperty()
    
    def __init__(self, *args, **kwargs):
        # this loads everything to self that's passed as a kwarg, making required and default attribs safe to use
        GeoModel.__init__(self, *args, **kwargs)
        if "location" in kwargs:
            self.update_location()
        self.update_slugs()
        
    def __str__(self):
        return "%s in %s, %s (%s)" % (self.name, self.city, self.state, self.country)
        
    def update_slugs(self):
        self.nameslug = slugify(self.name)
        self.cityslug = slugify(self.city)
        self.stateslug = slugify(self.state)
        self.countryslug = slugify(self.country)
        self.urlslug = "%s/%s/%s/%s"%(self.countryslug,self.stateslug,self.cityslug,self.nameslug)
    
    def to_jsonable(self):
        return {
            'ntd_id':self.ntd_id,
            'gtfs_data_exchange_id':self.gtfs_data_exchange_id,
            'date_opened':self.date_opened.isoformat(" ") if self.date_opened else None,
            'passenger_miles':self.passenger_miles,
            'is_public':self.is_public,
            'name': cgi.escape(self.name),
            'city': cgi.escape(self.city),
            'urlslug': self.urlslug,
            'state': cgi.escape(self.state),
            'details_url': self.details_url,
            'key_encoded': str(self.key()),
            'has_real_time_data': self.has_real_time_data,
            'latitude':self.location.lat,
            'longitude':self.location.lon,
        }

    @staticmethod
    def fetch_all_agencies_as_jsonable():
        memcache_key = "all-agencies-as-jsonable"
        all_as_jsonable = memcache.get(memcache_key)
        if all_as_jsonable is None:
            all_as_jsonable = [agency.to_jsonable() for agency in Agency.all()]
            memcache.set(memcache_key, all_as_jsonable, time = settings.MEMCACHE_DEFAULT_SECONDS)
        return all_as_jsonable

    @property
    def details_url(self):
        return reverse("agencies_all_slugs", kwargs={"countryslug": self.countryslug, "stateslug": self.stateslug, "cityslug": self.cityslug, "nameslug": self.nameslug})
                
    @property
    def is_public(self):
        return (self.date_opened != None)

    @staticmethod
    def fetch_agencies_near(latitude, longitude, query = None, max_results = 50, bbox_side_in_miles = settings.BBOX_SIDE_IN_MILES):
        bounding_box = square_bounding_box_centered_at(latitude, longitude, bbox_side_in_miles)
        if query is None:
            query = Agency.all()
        return Agency.bounding_box_fetch(query, bounding_box, max_results = max_results)        
        
    @property
    def has_real_time_data(self):
        return (self.arrival_data != None) or (self.position_data != None)
        
    @staticmethod
    def all_public_agencies():
        """Return a query to all Agency entities marked 'public' by Brandon's import scripts."""
        return Agency.all().filter('date_opened !=', None)

    @staticmethod    
    def get_state_list():
        #factoring this out since we want all states all the time
        #and because we want to memcache this
        #todo: add other countries (return dict where value includes proper url)
        mem_result = memcache.get('all_states')
        if not mem_result:
            states = uniquify([(a.countryslug,a.stateslug) for a in Agency.all()])
            states.sort(key=lambda x:x[1])
            mc_added = memcache.add('all_states', states, settings.MEMCACHE_DEFAULT_SECONDS)
        else:
            states = mem_result

        return states
        
    @staticmethod    
    def get_country_list():
        #factoring this out since we want all states all the time
        #and because we want to memcache this
        #todo: add other countries (return dict where value includes proper url)
        mem_result = memcache.get('all_countries')
        if not mem_result:
            countries = uniquify([a.countryslug for a in Agency.all()])
            countries.sort()
            mc_added = memcache.add('all_countries', countries, settings.MEMCACHE_DEFAULT_SECONDS)
        else:
            countries = mem_result

        return countries
    
    @staticmethod
    def fetch_for_slugs(countryslug = None, stateslug = None, cityslug = None):
        agency_query = Agency.all()        
        if cityslug:
            agency_query = agency_query.filter('cityslug =', cityslug)            
        if stateslug:
            agency_query = agency_query.filter('stateslug =', stateslug)            
        if countryslug:
            agency_query = agency_query.filter('countryslug =',countryslug)            
        return [agency for agency in agency_query]
    
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
    def fetch_for_transit_app(transit_app, uniquify = True):
        """Return a list of Agency entities, by default unique, that the given transit app supports"""
        return [agency for agency in Agency.iter_for_transit_app(transit_app, uniquify)]
        
    @staticmethod
    def iter_for_transit_app(transit_app, uniquify = True):
        """Return an iterator over Agency entities, by default unique, that the given transit app supports"""
        seen_set = set()
        for explicit_agency in iter_uniquify(Agency.iter_explicitly_supported_for_transit_app(transit_app), seen_set, uniquify):
            yield explicit_agency
        if transit_app.supports_all_public_agencies:
            for public_agency in iter_uniquify(Agency.all_public_agencies(), seen_set, uniquify):
                yield public_agency
        
    @staticmethod
    def fetch_for_transit_apps(transit_apps, uniquify = True):
        """Return a list of Agency entities, by default unique, that at least one transit application in the transit_apps list supports."""
        return [agency for agency in Agency.iter_for_transit_apps(transit_apps, uniquify)]

    @staticmethod
    def iter_for_transit_apps(transit_apps, uniquify = True):
        """Return an iterator over Agency entities, by default unique, that at least one transit application in the transit_apps list supports."""
        seen_set = set()
        for transit_app in transit_apps:
            for agency in iter_uniquify(Agency.iter_for_transit_app(transit_app, uniquify = False), seen_set, uniquify):
                yield agency        
