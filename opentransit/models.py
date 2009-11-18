import logging
from google.appengine.ext import db
from django.core.urlresolvers import reverse
from geo.geomodel import GeoModel
from .utils.slug import slugify
from .utils.datastore import normalize_to_key, normalize_to_keys, unique_entities

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
        """Return a query to all Agency entities marked 'public' by Brandon's import scripts."""
        return Agency.all().filter('is_public =', True)
        
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
    title               = db.StringProperty(required = True)
    description         = db.StringProperty()
    url                 = db.LinkProperty()
    author_name         = db.StringProperty()
    author_email        = db.EmailProperty()
    long_description    = db.TextProperty()
    tags                = db.StringListProperty()
    screen_shot         = db.BlobProperty()
    
    supports_all_public_agencies = db.BooleanProperty(indexed = True)
    explicitly_supported_agency_keys = db.ListProperty(db.Key)
    
    def __init__(self, *args, **kwargs):
        super(TransitApp, self).__init__(*args, **kwargs)
        self.slug = slugify(self.title)
    
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

    @staticmethod
    def all_supporting_public_agencies():
        """Return a query to all TransitApp entities flagged as supporting Agencies with 'public' data."""
        return TransitApp.all().filter('supports_all_public_agencies = ', True)
        
    @staticmethod
    def fetch_for_agency(agency_or_key, uniqify = True):
        """Return a list of TransitApp entities, by default unique, that support the given agency."""
        return [transit_app for transit_app in TransitApp.iter_for_agency(agency_or_key, uniqify)]
        
    @staticmethod
    def iter_for_agency(agency_or_key, uniqify = True):
        """Return an iterator over TransitApp entities, by default unique, that support the given agency."""
        seen = {}
        if isinstance(agency_or_key, db.Model):
            agency = agency_or_key
            agency_key = agency.key()
        else:
            agency = Agency.get([agency_or_key])
            agency_key = agency_or_key        
        for transit_app_with_explicit_support in TransitApp.gql('WHERE explicitly_supported_agency_keys = :1', agency_key):
            if (not uniqify) or (transit_app_with_explicit_support.key() not in seen):
                if uniqify: seen[transit_app_with_explicit_support.key()] = True
                yield transit_app_with_explicit_support        
        if agency.is_public:
            for transit_app_with_public_support in TransitApp.all_supporting_public_agencies():
                if (not uniqify) or (transit_app_with_public_support.key() not in seen):
                    if uniqify: seen[transit_app_with_public_support.key()] = True
                    yield transit_app_with_public_support

    @staticmethod
    def fetch_for_agencies(agencies_or_keys, uniqify = True):
        """Return a list of TransitApp entities, by default unique, that support at least one of the given agencies."""
        return [transit_app for transit_app in TransitApp.iter_for_agencies(agencies_or_keys, uniqify)]
        
    @staticmethod
    def iter_for_agencies(agencies_or_keys, uniqify = True):
        """Return an iterator over TransitApp entities, by default unique, that support at least one of the given agencies."""
        seen = {}
        for agency_or_key in agencies_or_keys:
            for transit_app in TransitApp.iter_for_agency(agency_or_key, uniqify = False):
                if (not uniqify) or (transit_app.key() not in seen):
                    if uniqify: seen[transit_app.key()] = True
                    yield transit_app

    def add_explicitly_supported_agencies(self, agencies_or_keys):
        """Helper to add new supported agencies to this transit app. You must call put() sometime later."""
        agency_keys = normalize_to_keys(agencies_or_keys)
        self.explicitly_supported_agency_keys.extend(agency_keys)

    def add_explicitly_supported_agency(self, agency_or_key):
        """Helper to add a single supported agency to this transit app. You must call put() sometime later."""
        self.add_explicitly_supported_agencies([agency_or_key])

    def remove_explicitly_supported_agencies(self, agencies_or_keys):
        """Helper to remove supported agencies from this transit app. You must call put() sometime later."""
        agency_keys = normalize_to_keys(agencies_or_keys)
        for agency_key in agency_keys:
            self.explicitly_supported_agency_keys.remove(agency_key)

    def remove_explicitly_supported_agency(self, agency_or_key):
        """Helper to remove supported agencies from this transit app. You must call put() sometime later."""
        self.remove_explicitly_supported_agencies([agency_or_key])
