import logging
from uuid import uuid4
from google.appengine.ext import db
from django.core.urlresolvers import reverse
from geo.geomodel import GeoModel
from .agency import Agency
from ..utils.slug import slugify
from ..utils.datastore import key_and_entity, normalize_to_key, normalize_to_keys, unique_entities

#
# A brief explanation of how Transit Apps and Agencies relate:
#
# We have two 'kinds' of connection from a transit application to an agency.
#
# First, transit apps can support "all public agencies." As our list of public agencies grows,
# these apps should automatically reflect this. Therefore, we keep a boolean value around.
#
# At the same time, apps can explicitly support other agencies. Here we have a many-many
# relationship. Because the typical transit app probably won't have support for a large number
# of agencies, we don't have a separate "join" model. Instead we keep a (presumed
# small) list of agency keys in each transit app.
#
# There are corresponding APIs to get all transit applications for a given agency, too.
#
# With all of these APIs, you must call put() afterward.
#
# -----
# 
# And ANOTHER brief explanation of why Transit Apps have their own "location" information:
#
# A lot of transit apps don't associate directly with agencies. For example, an app that supports
# bike riders wouldn't use GTFS feeds. So it doesn't make sense to have agencies be the _only_ way
# to "locate" where a transit app is useful.
#
# Therefore, we also keep a list of supported cities and countries for each transit app.
# These are canonicalized country codes and city names returned from Google's GeoCode APIs.
#
# "explicitly_supported_cities" holds on to the city names. For each explicitly supported city,
# there is also a TransitAppLocation GeoModel in the data store to allow for finding transit apps
# in nearby cities.
# 
# "explcitily_supported_countries" holds on to counry codes. Unlike cities, there is no 
# corresponding TransitAppLocation entry (what would the location be, anyway?)
#
# -----
# 
# In total, what queries do we have to perform to identify nearby applications
# when user searches at a particular lat/lon, and with a particular country code?
#
# 1. What agencies are nearby lat/lon? 
#       And then, what transit apps support those agencies?
# 2. What transit apps are nearby lat/lon?
# 3. What transit apps support that country code?
# 4. What transit apps support the entire GLOBE?
# 
# Can we simplify this? It seems like #1 and #2 are basically the same. But the trick is
# that we have the `supports_all_public_agencies` flag. If a public agency is nearby, this
# effectively lights up a ton of new applications. So #1 has to take this into account, but
# #2 does not. I don't see a way around this while still keeping our simpler data model.
# (We could very easily do this better if we explicitly associated each transit app with _all_
# agencies, including public ones, rather than maintaining a flag. But I think that could get
# problematic in other ways...)
#

class TransitApp(db.Model):
    PLATFORMS = { 
        "android": "Android", 
        "blackberry": "Blackberry",
        "iphone": "iPhone", 
        "mobile_web": "Mobile Web",
        "palm_webos": "Palm WebOS", 
        "sms": "SMS",
        "other": "Other",
    }
    
    CATEGORIES = {
        "public_transit": "Public Transit", 
        "driving": "Driving", 
        "biking": "Biking", 
        "walking": "Walking",
    }
        
    @staticmethod 
    def platform_choices():
        if hasattr(TransitApp, '_platform_choices'):
            return TransitApp._platform_choices
        choices = [(short_name, label) for short_name, label in TransitApp.PLATFORMS.iteritems()]
        choices.sort()
        TransitApp._platform_choices = choices
        return choices
    
    @staticmethod
    def category_choices():
        if hasattr(TransitApp, '_category_choices'):
            return TransitApp._category_choices
        choices = [(short_name, label) for short_name, label in TransitApp.CATEGORIES.iteritems()]
        choices.sort()
        TransitApp._category_choices = choices
        return choices
        
    @staticmethod
    def gtfs_choices():
        return [("yes_gtfs", "My application makes use of GTFS feeds."), ("no_gtfs", "My application does not make use of GTFS feeds.")]
    
    @staticmethod
    def gtfs_public_choices():
        return [("yes_public", "My application supports all publicly available GTFS feeds."), ("no_public", "My application supports specific GTFS feeds. Let me choose them.")]
        
    slug                = db.StringProperty(indexed = True)
    title               = db.StringProperty(required = True)
    description         = db.StringProperty()
    url                 = db.LinkProperty()
    author_name         = db.StringProperty()
    author_email        = db.EmailProperty()
    long_description    = db.TextProperty()
    tags                = db.StringListProperty()
    screen_shot         = db.BlobProperty()
    platforms           = db.StringListProperty() # These also go into tags, automatically
    categories          = db.StringListProperty() # These also go into tags, automatically    
    
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

    supports_all_public_agencies = db.BooleanProperty(indexed = True)
    explicitly_supported_agency_keys = db.ListProperty(db.Key)
    explicitly_supported_cities = db.StringListProperty(indexed = True)   # ["Seattle", "San Francisco", ...]
    explicitly_supported_city_details = db.StringListProperty() # ["Seattle,WA,US", "San Francisco,CA,US", ...]
    explicitly_supported_countries = db.StringListProperty()
    explicitly_supports_the_entire_world = db.BooleanProperty(indexed = True)
                
    @staticmethod
    def all_supporting_public_agencies():
        """Return a query to all TransitApp entities flagged as supporting Agencies with 'public' data."""
        return TransitApp.all().filter('supports_all_public_agencies = ', True)
        
    @staticmethod
    def fetch_for_agency(agency_or_key, uniquify = True):
        """Return a list of TransitApp entities, by default unique, that support the given agency."""
        return [transit_app for transit_app in TransitApp.iter_for_agency(agency_or_key, uniquify)]
        
    @staticmethod
    def iter_for_agency(agency_or_key, uniquify = True):
        """Return an iterator over TransitApp entities, by default unique, that support the given agency."""
        seen = {}
        agency_key, agency = key_and_entity(agency_or_key, Agency)
        for transit_app_with_explicit_support in TransitApp.gql('WHERE explicitly_supported_agency_keys = :1', agency_key):
            if (not uniquify) or (transit_app_with_explicit_support.key() not in seen):
                if uniquify: seen[transit_app_with_explicit_support.key()] = True
                yield transit_app_with_explicit_support        
        if agency.is_public:
            for transit_app_with_public_support in TransitApp.all_supporting_public_agencies():
                if (not uniquify) or (transit_app_with_public_support.key() not in seen):
                    if uniquify: seen[transit_app_with_public_support.key()] = True
                    yield transit_app_with_public_support

    @staticmethod
    def fetch_for_agencies(agencies_or_keys, uniquify = True):
        """Return a list of TransitApp entities, by default unique, that support at least one of the given agencies."""
        return [transit_app for transit_app in TransitApp.iter_for_agencies(agencies_or_keys, uniquify)]
        
    @staticmethod
    def iter_for_agencies(agencies_or_keys, uniquify = True):
        """Return an iterator over TransitApp entities, by default unique, that support at least one of the given agencies."""
        seen = {}
        for agency_or_key in agencies_or_keys:
            for transit_app in TransitApp.iter_for_agency(agency_or_key, uniquify = False):
                if (not uniquify) or (transit_app.key() not in seen):
                    if uniquify: seen[transit_app.key()] = True
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
        
    @staticmethod
    def all_for_country(coutry_code):
        return TransitApp.gql('WHERE supported_countries = :1', country_code)
        
    @staticmethod
    def all_for_city(city):
        return TransitApp.gql('WHERE supported_cities = :1', city)
    
    @staticmethod
    def iter_for_country_or_city(country_code = None, city = None, uniquify = True):
        seen = {}        
        if city:
            for transit_app in TransitApp.all_for_city(city):
                if (not uniquify) or (transit_app.key() not in seen):
                    if uniquify: seen[transit_app.key()] = True
                    yield transit_app
        if country:
            for transit_app in TransitApp.all_for_country(country_code):
                if (not uniquify) or (transit_app.key() not in seen):
                    if uniquify: seen[transit_app.key()] = True
                    yield transit_app
    
    @staticmethod
    def iter_for_country_and_city(country_code, city):
        seen_city = {}
        for transit_app in TransitApp.all_for_city(city):
            seen_city[transit_app.key()] = True
        for transit_app in TransitApp.all_for_country(country_code):
            if transit_app.key() in seen_city:
                yield transit_app
    
class TransitAppLocation(GeoModel):
    """Represents a many-many relationship between TransitApps and explcitly named cities where they work."""
    transit_app = db.ReferenceProperty(TransitApp, collection_name = "explicitly_supported_locations")

class TransitAppFormProgress(db.Model):
    """Holds on to key pieces of form progress that cannot be sent through invisible input fields."""
    progress_uuid = db.StringProperty(indexed = True, required = True)
    last_updated = db.DateTimeProperty(auto_now = True)    
    info_form_pickle = db.BlobProperty() # dictionary of stuff from original form, pickled.
    screen_shot = db.BlobProperty()

    @staticmethod
    def new_with_uuid():
        return TransitAppFormProgress(progress_uuid = str(uuid4()).replace('-', ''))
    
    @staticmethod
    def get_with_uuid(uuid):
        return TransitAppFormProgress.all().filter('progress_uuid =', uuid).get()

