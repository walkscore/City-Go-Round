import logging
from uuid import uuid4
from decimal import Decimal
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.safestring import SafeString
from google.appengine.ext import db
from geo.geomodel import GeoModel
from .agency import Agency
from .imageblob import ImageBlob
from ..properties import DecimalProperty
from ..utils.slug import slugify
from ..utils.datastore import key_and_entity, normalize_to_key, normalize_to_keys, unique_entities, iter_uniquify
from ..utils.places import CityInfo
from ..utils.geohelpers import square_bounding_box_centered_at
from ..utils.misc import key_for_value
from ..models import NamedStat
import cgi


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
        "android": "Android App", 
        "blackberry": "Blackberry App",
        "iphone": "iPhone App", 
        "palm_webos": "Palm WebOS App", 
        "sms": "SMS",
        "web": "Website (Desktop/Laptop)",
        "mobile_web": "Website (Mobile-Optimized)",
        "other": "Other",
    }
    
    CATEGORIES = {
        "public_transit": "Public Transit", 
        "driving": "Driving", 
        "biking": "Biking", 
        "walking": "Walking",
    }
    
    SCREEN_SHOT_SIZES = [
        ("original", ImageBlob.ORIGINAL_SIZE),
        ("300w", (300, 0)),
        ("145w", (145, 0)),
        ("180sq", (180, 180)),
        ("80sq", (80, 80)),
    ]
                    
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
        return [
            ("nothing", "My application does not use transit data."), 
            ("specific_agencies", "My application uses transit data from specific agencies. (Select from list below.)"),
            ("public_agencies", SafeString('My application uses transit data from all transit agencies with public <a href="http://code.google.com/transit/spec/transit_feed_specification.html" target="_blank">GTFS feeds</a>.<br /></li><strong>Note:</strong> Choose this option if your app automatically adds new GTFS feeds from transit agencies as they are made available.  If you choose this option, your app will be associated with every public feed listed on the <a href="http://www.gtfs-data-exchange.com/" target="_blank">GTFS Data Exchange</a>.')), 
        ]
        
    @staticmethod
    def screen_shot_size_from_name(size_name):
        for name, (width, height) in TransitApp.SCREEN_SHOT_SIZES:
            if name == size_name:
                return (width, height)
        return (0, 0)
    
    @staticmethod
    def screen_shot_name_from_size(size):
        for name, (width, height) in TransitApp.SCREEN_SHOT_SIZES:
            if (width, height) == size:
                return name
        
    slug                = db.StringProperty(indexed = True)
    title               = db.StringProperty(required = True)
    description         = db.StringProperty()
    url                 = db.LinkProperty()
    price               = DecimalProperty()
    author_name         = db.StringProperty()
    author_email        = db.EmailProperty()
    long_description    = db.TextProperty()
    tags                = db.StringListProperty()
    platforms           = db.StringListProperty() # These also go into tags, automatically
    categories          = db.StringListProperty() # These also go into tags, automatically  
    date_added          = db.DateTimeProperty(auto_now_add = True, indexed = True)
    date_last_updated   = db.DateTimeProperty(auto_now = True, indexed = True)
    is_featured         = db.BooleanProperty(indexed = True, default = False)
    screen_shot_families = db.StringListProperty() # Ordered list of screen shot families, length >= 1
    rating_sum          = db.FloatProperty(default=0.0)
    rating_count        = db.IntegerProperty(default=0)
    bayesian_average    = db.FloatProperty()
    is_hidden           = db.BooleanProperty(indexed = True, default = False)
    
    screen_shot         = db.BlobProperty() # THIS FIELD IS DEPRECATED. DO NOT USE IT. IT IS KEPT ONLY FOR BACKWARDS COMPAT.
    
    def __init__(self, *args, **kwargs):
        super(TransitApp, self).__init__(*args, **kwargs)
        self.slug = slugify(self.title)
    
    def __str__(self):
        return "%s (%s)" % (self.title, self.url)
    
    def to_jsonable(self, include_visibility = False):
        jsonable = {
            "title": cgi.escape(self.title),
            "slug": self.slug,
            "description": cgi.escape(self.description),
            "rating": self.average_rating,
            "rating_count": self.rating_count,
            "url": str(self.url),
            "price": str(self.price),
            "is_free": self.is_free,
            "author_name": cgi.escape(str(self.author_name)), # DO NOT INCLUDE AUTHOR EMAIL.
            "long_description": cgi.escape(self.long_description),
            "tags": [cgi.escape(tag) for tag in self.tags], # NOTE davepeck: while editing code near here, I filed CGR Bug 117 about this line of code.
            "platforms": [cgi.escape(platform) for platform in self.platforms], # NOTE davepeck: while editing code near here, I filed CGR Bug 117 about this line of code.
            "is_featured": self.is_featured,
            "details_url": self.details_url,
            "bayesian_average": self.bayesian_average,
            "average_rating_out_of_80": self.average_rating_out_of_80,
            "categories": [category for category in self.categories], # Note that bug 117 doesn't apply here -- I don't escape this.
            "default_300w_screen_shot_url": self.default_300w_screen_shot_url,
            "default_145w_screen_shot_url": self.default_145w_screen_shot_url,
            "default_180sq_screen_shot_url": self.default_180sq_screen_shot_url,
            "default_80sq_screen_shot_url": self.default_80sq_screen_shot_url,
        }
        
        if include_visibility:
            jsonable["is_hidden"] = self.is_hidden
        
        return jsonable

    @staticmethod
    def query_all(visible_only = True):
        query = TransitApp.all()
        if visible_only: query = query.filter('is_hidden =', False)
        return query
        
    @property
    def is_free(self):
        return (self.price == Decimal("0"))
        
    @property
    def screen_shot_count(self):
        return len(self.screen_shot_families)
    
    @property
    def screen_shot_indexes(self):
        """For use in template for loops."""
        return range(self.screen_shot_count)
        
    @property
    def screen_shot_non_default_indexes(self):
        """For use in template for loops."""
        return range(1, self.screen_shot_count)
        
    def screen_shots_to_jsonable(self):
        shots = []
        index = 0
        for screen_shot_family in self.screen_shot_families:
            dictionary = {
                "family": screen_shot_family,
            }
            for size_name, (width, height) in TransitApp.SCREEN_SHOT_SIZES:
                dictionary["url_" + size_name] = self.get_screen_shot_url(index, size_name = size_name)
            shots.append(dictionary)
            index += 1
        return shots
        
    def get_screen_shot_url(self, index, width = None, height = None, size = None, size_name = None):
        if (width is not None) and (height is not None):
            size_name = TransitApp.screen_shot_name_from_size((width, height))
        elif size is not None:
            size_name = TransitApp.screen_shot_name_from_size(size)
        return reverse('apps_screenshot', kwargs = {'transit_app_slug': self.slug, 'screen_shot_index': index, 'screen_shot_size_name': size_name})
        
    def _resolve_screen_shot(self, index, width = None, height = None, size = None, size_name = None):
        if size is not None:
            width, height = size
        elif size_name is not None:
            width, height = TransitApp.screen_shot_size_from_name(size_name)
        family = self.screen_shot_families[index]        
        return (family, width, height)
                
    def has_screen_shot(self, index, width = None, height = None, size = None, size_name = None):
        try:
            family, width, height = self._resolve_screen_shot(index = index, width = width, height = height, size = size, size_name = size_name)
        except (ValueError, IndexError):
            return False
        return True
        
    def get_screen_shot_bytes_and_extension(self, index, width = None, height = None, size = None, size_name = None):
        try:
            family, width, height = self._resolve_screen_shot(index = index, width = width, height = height, size = size, size_name = size_name)
        except (ValueError, IndexError):
            return (None, None)
        return ImageBlob.get_bytes_and_extension_for_family_and_size(family, (width, height))
        
    @property
    def default_300w_screen_shot_url(self):
        return self.get_screen_shot_url(index = 0, size = TransitApp.screen_shot_size_from_name("300w"))

    @property
    def default_145w_screen_shot_url(self):
        return self.get_screen_shot_url(index = 0, size = TransitApp.screen_shot_size_from_name("145w"))

    @property
    def default_180sq_screen_shot_url(self):
        return self.get_screen_shot_url(index = 0, size = TransitApp.screen_shot_size_from_name("180sq"))
        
    @property
    def default_80sq_screen_shot_url(self):
        return self.get_screen_shot_url(index = 0, size = TransitApp.screen_shot_size_from_name("80sq"))
                    
    @property
    def details_url(self):
        return reverse("apps_details", kwargs = {'transit_app_slug': self.slug})
                
    @staticmethod
    def all_by_most_recently_added(visible_only = True):
        return TransitApp.query_all(visible_only = visible_only).order('-date_added')
        
    @staticmethod
    def featured_by_most_recently_added(visible_only = True):
        return TransitApp.query_all(visible_only = visible_only).filter('is_featured =', True).order('-date_added')
        
    @staticmethod
    def transit_app_for_slug(transit_app_slug, visible_only = True): 
        return TransitApp.query_all(visible_only = visible_only).filter('slug =', transit_app_slug).get()
    
    @staticmethod
    def has_transit_app_for_slug(transit_app_slug, visible_only = True):
        return (TransitApp.transit_app_for_slug(transit_app_slug, visible_only = visible_only) is not None)

    @property
    def tag_list_as_string(self):
        unique_tags = []
        for tag in self.tags:
            if (tag not in TransitApp.CATEGORIES.values()) and (tag not in TransitApp.PLATFORMS.values()):
                unique_tags.append(tag)
        return ', '.join(unique_tags)
    
    @property
    def category_choice_list(self):
        return [key_for_value(TransitApp.CATEGORIES, category) for category in self.categories]
    
    @property
    def platform_choice_list(self):
        platforms = [key_for_value(TransitApp.PLATFORMS, platform) for platform in self.platforms]
        platforms.sort()
        return platforms

    supports_any_gtfs = db.BooleanProperty(default = False)
    supports_all_public_agencies = db.BooleanProperty(default = False, indexed = True)
    explicitly_supported_agency_keys = db.ListProperty(db.Key)
    explicitly_supported_city_slugs = db.StringListProperty(indexed = True)   # ["seattle", "san-francisco", ...]
    explicitly_supported_city_details = db.StringListProperty() # ["Seattle,WA,US", "San Francisco,CA,US", ...]
    explicitly_supported_countries = db.StringListProperty() # ["US", "DE", ...]
    explicitly_supports_the_entire_world = db.BooleanProperty(default = False, indexed = True)
            
    @staticmethod
    def all_sorted_by_rating(visible_only = True):
        return TransitApp.query_all(visible_only = visible_only).order('-bayesian_average')
        
    @staticmethod
    def fetch_all_sorted_by_rating(visible_only = True):
        return [transit_app for transit_app in TransitApp.all_sorted_by_rating(visible_only = visible_only)]
            
    @staticmethod
    def all_supporting_public_agencies(visible_only = True):
        """Return a query to all TransitApp entities flagged as supporting Agencies with 'public' data."""
        return TransitApp.query_all(visible_only = visible_only).filter('supports_all_public_agencies = ', True)
        
    @staticmethod
    def fetch_for_explicit_agency(agency_or_key, uniquify = True, visible_only = True):
        """Return a list of TransitApp entities, by default unique, that have explicit support for the given agency."""
        return [transit_app for transit_app in TransitApp.iter_for_explicit_agency(agency_or_key, uniquify, visible_only)]
    
    @staticmethod
    def iter_for_explicit_agency(agency_or_key, uniquify = True, visible_only = True):
        """Return an iterator over TransitApp entities, by default unique, that have explicit support for the given agency."""
        seen_set = set()
        agency_key, agency = key_and_entity(agency_or_key, Agency)
        for transit_app_with_explicit_support in iter_uniquify(TransitApp.query_all(visible_only = visible_only).filter('explicitly_supported_agency_keys =', agency_key), seen_set, uniquify):
            yield transit_app_with_explicit_support            
    
    @staticmethod
    def fetch_for_agency(agency_or_key, uniquify = True, visible_only = True):
        """Return a list of TransitApp entities, by default unique, that support the given agency."""
        return [transit_app for transit_app in TransitApp.iter_for_agency(agency_or_key, uniquify, visible_only)]
        
    @staticmethod
    def iter_for_agency(agency_or_key, uniquify = True, visible_only = True):
        """Return an iterator over TransitApp entities, by default unique, that support the given agency."""
        seen_set = set()
        agency_key, agency = key_and_entity(agency_or_key, Agency)
        for transit_app_with_explicit_support in iter_uniquify(TransitApp.query_all(visible_only = visible_only).filter('explicitly_supported_agency_keys =', agency_key), seen_set, uniquify):
            yield transit_app_with_explicit_support        
        if agency.is_public:
            for transit_app_with_public_support in iter_uniquify(TransitApp.all_supporting_public_agencies(visible_only = visible_only), seen_set, uniquify):
                yield transit_app_with_public_support

    @staticmethod
    def fetch_for_agencies(agencies_or_keys, uniquify = True, visible_only = True):
        """Return a list of TransitApp entities, by default unique, that support at least one of the given agencies."""
        return [transit_app for transit_app in TransitApp.iter_for_agencies(agencies_or_keys, uniquify, visible_only)]
        
    @staticmethod
    def iter_for_agencies(agencies_or_keys, uniquify = True, visible_only = True):
        """Return an iterator over TransitApp entities, by default unique, that support at least one of the given agencies."""
        seen_set = set()
        for agency_or_key in agencies_or_keys:
            for transit_app in iter_uniquify(TransitApp.iter_for_agency(agency_or_key, uniquify = False, visible_only = visible_only), seen_set, uniquify):
                yield transit_app
        
    def get_supported_location_list(self):
        list = self.explicitly_supported_city_details + self.explicitly_supported_countries
        return list

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
        
    def add_explicitly_supported_city_info(self, city_info):
        """Returns a new TransitAppLocation instance that you must put(); helper to set up relations for city information."""
        if not isinstance(city_info, CityInfo):
            raise Exception("You must pass in a CityInfo object.")
        self.explicitly_supported_city_slugs.append(city_info.name_slug)
        self.explicitly_supported_city_details.append(city_info.important_details)
        return TransitAppLocation(transit_app = self.key(), city_slug = city_info.name_slug, city_details = city_info.important_details, location = db.GeoPt(city_info.latitude, city_info.longitude))
        
    def add_explicitly_supported_city_info_lazy(self, city_info):
        """Helper to set up relations for city information. Returns a function that will create a corresponding transit app location. You must put() that."""
        if not isinstance(city_info, CityInfo):
            raise Exception("You must pass in a CityInfo object.")
        self.explicitly_supported_city_slugs.append(city_info.name_slug)
        self.explicitly_supported_city_details.append(city_info.important_details)
        return lambda: TransitAppLocation(transit_app = self.key(), city_slug = city_info.name_slug, city_details = city_info.important_details, location = db.GeoPt(city_info.latitude, city_info.longitude))
        
    def add_explicitly_supported_city_info_immediate(self, city_info):
        """Helper to set up relations for city information. Immediately adds the TransitAppLocation object to the data store."""
        self.add_explicitly_supported_city_info(city_info).put()

    def add_explicitly_supported_city_infos(self, city_infos):
        """Returns a list of new TransitAppLocation instances that you must put(); helper to set up relations for city informations."""
        return [self.add_explicitly_supported_city_info(city_info) for city_info in city_infos]
        
    def add_explicitly_supported_city_infos_lazy(self, city_infos):
        """Returns a list of new TransitAppLocation functions that you must invoke and then put(); helper to set up relations for city informations."""
        return [self.add_explicitly_supported_city_info_lazy(city_info) for city_info in city_infos]
    
    def add_explicitly_supported_city_infos_immedate(self, city_infos):
        """Helper to set up relations for city informations. Immediately adds the TransitAppLocation objects to the data store."""
        transit_app_locations = self.add_explicitly_supported_city_infos(city_infos)
        db.put(transit_app_locations)
    
    def add_explicitly_supported_country(self, country_code):
        self.explicitly_supported_countries.append(country_code)
        
    def add_explicitly_supported_countries(self, country_codes):
        self.explicitly_supported_countries.extend(country_codes)
        
    def add_rating(self, rating):
        self.rating_sum += rating
        self.rating_count += 1
        
    @property
    def average_rating(self):
        if self.rating_count==0:
            return None
        return self.rating_sum/self.rating_count
        
    @property
    def average_rating_integer(self):
        if self.rating_count==0:
            return 0
        return int(self.rating_sum*10/self.rating_count)
        
    @property
    def average_rating_out_of_80(self):
        if self.rating_count==0:
            return 0
        return int( (self.rating_sum * 79.0) / ( self.rating_count*5.0) )
        
    @property
    def num_ratings(self):
        return self.rating_count
    
    def refresh_bayesian_average(self, all_rating_sum=None, all_rating_count=None):
        all_rating_sum = all_rating_sum or NamedStat.get_stat( "all_rating_sum" )
        all_rating_count = all_rating_count or NamedStat.get_stat( "all_rating_count" )
        
        Cm = all_rating_sum.value
        sumx = self.rating_sum
        n = self.rating_count
        C = all_rating_count.value
        
        if (n+C)>0:
            bayesian_average = (Cm + sumx)/float(n+C)
        else:
            bayesian_average = None
        self.bayesian_average = bayesian_average
        
    @staticmethod
    def all_for_country(country_code, visible_only = True):
        return TransitApp.query_all(visible_only = visible_only).filter('explicitly_supported_countries =', country_code)
        
    @staticmethod
    def all_for_city(city, visible_only = True):
        return TransitApp.query_all(visible_only = visible_only).filter('explicitly_supported_city_slugs =', slugify(city))
    
    @staticmethod
    def all_with_support_for_entire_world(visible_only = True):
        return TransitApp.query_all(visible_only = visible_only).filter('explicitly_supports_the_entire_world =', True)
    
    @staticmethod
    def iter_for_country_or_city(country_code = None, city = None, uniquify = True, visible_only = True):
        seen_set = set()        
        if city:
            for transit_app in iter_uniquify(TransitApp.all_for_city(city, visible_only = visible_only), seen_set, uniquify):
                yield transit_app
        if country:
            for transit_app in iter_uniquify(TransitApp.all_for_country(country_code, visible_only = visible_only), seen_set, uniquify):
                yield transit_app
    
    @staticmethod
    def iter_for_country_and_city(country_code, city, visible_only = True):
        seen_city = {}
        for transit_app in TransitApp.all_for_city(city, visible_only = visible_only):
            seen_city[transit_app.key()] = True
        for transit_app in TransitApp.all_for_country(country_code, visible_only = visible_only):
            if transit_app.key() in seen_city:
                yield transit_app

    @staticmethod
    def fetch_transit_apps_near(latitude, longitude, max_results = 500, bbox_side_in_miles = settings.BBOX_SIDE_IN_MILES, visible_only = True):
        raw_transit_apps = [transit_app_location.transit_app for transit_app_location in TransitAppLocation.fetch_transit_app_locations_near(latitude, longitude, query = None, max_results = max_results, bbox_side_in_miles = bbox_side_in_miles)]
        return [transit_app for transit_app in raw_transit_apps if not (visible_only and transit_app.is_hidden)]
    
    @staticmethod
    def iter_for_location_and_country_code(latitude, longitude, country_code, bbox_side_in_miles = settings.BBOX_SIDE_IN_MILES, uniquify = True, visible_only = True):
        seen_set = set()
        
        # 1. What agencies are nearby lat/lon? 
        agencies_nearby = Agency.fetch_agencies_near(latitude, longitude, bbox_side_in_miles = bbox_side_in_miles)
        
        #    (And then, what transit apps support those agencies?)
        transit_apps_for_agencies = TransitApp.fetch_for_agencies(agencies_nearby, uniquify = False, visible_only = visible_only)
        for transit_app in iter_uniquify(transit_apps_for_agencies, seen_set, uniquify):
            yield transit_app
        
        # 2. What transit apps are explicitly nearby lat/lon?
        transit_apps_near = TransitApp.fetch_transit_apps_near(latitude, longitude, bbox_side_in_miles = bbox_side_in_miles, visible_only = visible_only)
        for transit_app in iter_uniquify(transit_apps_near, seen_set, uniquify):
            yield transit_app
        
        # 3. What transit apps support the country code in question?
        transit_apps_from_country_code = TransitApp.all_for_country(country_code, visible_only = visible_only)
        for transit_app in iter_uniquify(transit_apps_from_country_code, seen_set, uniquify):
            yield transit_app
        
        # 4. What transit apps support the entire GLOBE?
        transit_apps_with_world_support = TransitApp.all_with_support_for_entire_world(visible_only = visible_only)
        for transit_app in iter_uniquify(transit_apps_with_world_support, seen_set, uniquify):
            yield transit_app
        
    @staticmethod
    def fetch_for_location_and_country_code(latitude, longitude, country_code, bbox_side_in_miles = settings.BBOX_SIDE_IN_MILES, uniquify = True, visible_only = True):
        return [transit_app for transit_app in TransitApp.iter_for_location_and_country_code(latitude, longitude, country_code, uniquify = uniquify, bbox_side_in_miles = bbox_side_in_miles, visible_only = visible_only)]
            
    @staticmethod
    def count_apps_in_category(category, visible_only = True):
        return TransitApp.query_all(visible_only = visible_only).filter("categories =", category).count()
        
    @staticmethod
    def agency_app_counts(visible_only = True):
        #TODO: this always runs so slowly it times out
        ret = {}
        for agency in Agency.all():
            ret[str(agency.key())] = len(list(TransitApp.iter_for_agency(agency, visible_only = visible_only)))
        return ret


class TransitAppLocation(GeoModel):
    """Represents a many-many relationship between TransitApps and explcitly named cities where they work."""
    transit_app = db.ReferenceProperty(TransitApp, collection_name = "explicitly_supported_locations")
    city_slug = db.StringProperty()
    city_details = db.StringProperty()
    
    def __init__(self, *args, **kwargs):
        super(TransitAppLocation, self).__init__(*args, **kwargs)
        self.update_location()

    def __str__(self):
        return "lat: %.4f, lon: %.4f (for %s)" % (self.location.lat, self.location.lon, self.city_details)

    @staticmethod
    def fetch_transit_app_locations_near(latitude, longitude, query = None, max_results = 500, bbox_side_in_miles = settings.BBOX_SIDE_IN_MILES):
        bounding_box = square_bounding_box_centered_at(latitude, longitude, bbox_side_in_miles)
        if query is None:
            query = TransitAppLocation.all()
        return TransitAppLocation.bounding_box_fetch(query, bounding_box, max_results = max_results)


class TransitAppFormProgress(db.Model):
    """Holds on to key pieces of form progress that cannot be sent through invisible input fields."""
    progress_uuid = db.StringProperty(indexed = True, required = True)
    last_updated = db.DateTimeProperty(auto_now = True)    
    info_form_pickle = db.BlobProperty() # dictionary of stuff from original form, pickled.
    agency_form_pickle = db.BlobProperty() # dictionary of stuff from agency form, pickled.
    screen_shot_families = db.StringListProperty()

    @staticmethod
    def new_with_uuid():
        return TransitAppFormProgress(progress_uuid = str(uuid4()).replace('-', ''))
    
    @staticmethod
    def get_with_uuid(uuid):
        return TransitAppFormProgress.all().filter('progress_uuid =', uuid).get()
    