import logging
from google.appengine.ext import db
from django.core.urlresolvers import reverse
from geo.geomodel import GeoModel
from .utils.slug import slugify
from .utils.datastore import normalize_to_keys, unique_entities

class PetitionModel(db.Model):
    name        = db.StringProperty()
    email       = db.EmailProperty()
    city        = db.StringProperty()
    state       = db.StringProperty()
    country     = db.StringProperty()
    
class Agency(GeoModel):
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
    
    # is_public is True IF at least one of the feeds for this agency (--dave)
    # TODO bmander: keep this property up to date when you do the feed + agency work.
    is_public       = db.BooleanProperty(indexed = True)
    
    def __init__(self, *args, **kwargs):
        # this loads everything to self that's passed as a kwarg, making required and default attribs safe to use
        GeoModel.__init__(self, *args, **kwargs)
        
        self.nameslug = slugify(self.name)
        self.cityslug = slugify(self.city)
        self.stateslug = slugify(self.state)
        self.countryslug = slugify(self.country)
        self.urlslug = "%s/%s/%s/%s"%(self.countryslug,self.stateslug,self.cityslug,self.nameslug)
        
    @staticmethod
    def all_public_agencies():
        return Agency.all().filter('is_public =', True)
        
    @staticmethod
    def fetch_for_transit_app(transit_app, uniqify = True):
        fetched = []
        if transit_app.supports_all_public_agencies:
            for public_agency in Agency.all_public_agencies():
                fetched.append(public_agency)
        fetched.extend(transit_app.fetch_explicitly_supported_agencies())
        if uniqify:
            fetched = unique_entities(fetched)
        return fetched
        
    @staticmethod
    def iter_for_transit_app(transit_app, uniqify = True):
        seen = {}
        if transit_app.supports_all_public_agencies:
            for public_agency in Agency.all_public_agencies():
                if (not uniqify) or (public_agency.key() not in seen):
                    if uniqify: seen[public_agency.key()] = True
                    yield public_agency
        for explicit_agency in transit_app.iter_explicitly_supported_agencies():
            if (not uniqify) or (explicit_agency.key() not in seen):
                if uniqify: seen[explicit_agency.key()] = True
                yield explicit_agency
        
    @staticmethod
    def fetch_for_transit_apps(transit_apps, uniqify = True):
        fetched = []
        for transit_app in transit_apps:
            fetched.extend(Agency.fetch_for_transit_app(transit_app, uniqify = False))
        if uniqify:
            fetched = unique_entities(fetched)
        return fetched   

    @staticmethod
    def iter_for_transit_apps(transit_apps, uniqify = True):
        seen = {}
        for transit_app in transit_apps:
            for agency in Agency.iter_for_transit_app(transit_app, uniqify = False):
                if (not uniqify) or (agency not in seen):
                    if uniqify: seen[agency.key()] = True
                    yield agency        

        
class FeedReference(db.Model):
    """feed reference models a GTFS Data Exchange entity"""
    
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
        
        
    #
    # A brief explanation of the way this works:
    # We basically have two 'kinds' of connection from a transit application to an agency.
    #
    # First, transit apps can support "all public agencies." As our list of public agencies grows,
    # these apps should automatically reflect this. Therefore, we keep a boolean value around.
    #
    # At the same time, apps can explicitly support non-public agencies. Here we have a many-many
    # relationship. Because the typical transit app probably won't have support for a large number
    # of non-public agencies, we don't have a separate "join" model. Instead we keep a (presumed
    # small) list of agency keys in each transit app.
    #
    # There are corresponding APIs to get all transit applications for a given agency, too.
    #
    # With all of these APIs, you must call put() afterward.
    #
    # -Dave
    
    supports_all_public_agencies = db.BooleanProperty(indexed = True)
    explicitly_supported_agency_keys = db.ListProperty(db.Key)

    @staticmethod
    def all_supporting_public_agencies():
        
        pass
        
    @staticmethod
    def fetch_for_agency(agency):
        pass
        
    @staticmethod
    def fetch_for_agencies(agencies):
        pass

    @property
    def supported_agencies(self):
        pass # TODO davepeck

    def fetch_explicitly_supported_agencies(self):
        return Agency.get(self.explicitly_supported_agency_keys)
    
    def add_explicitly_supported_agencies(self, agencies_or_keys):
        agency_keys = normalize_to_keys(agencies_or_keys)
        self.explicitly_supported_agency_keys.extend(agency_keys)
        
    def add_explicitly_supported_agency(self, angency_or_key):
        self.add_explicitly_supported_agencies([agency_or_key])
        
    def remove_explicitly_supported_agencies(self, agencies_or_keys):
        agency_keys = normalize_to_keys(agencies_or_keys)
        for agency_key in agency_keys:
            self.explicitly_supported_agency_keys.remove(agency_key)
        