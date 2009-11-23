import time
import logging

from django.http import HttpResponse, HttpResponseRedirect

from google.appengine.ext import db
from google.appengine.api import memcache

from ..models import Agency, TransitApp
from ..utils.view import render_to_response, redirect_to, not_implemented, bad_request, method_not_allowed, render_to_json
from ..utils.slug import slugify
from ..utils.geohelpers import are_latitude_and_longitude_valid
from ..decorators import requires_valid_transit_app_slug, requires_valid_agency_key_encoded

def api_agencies_all(request):
    """
        Return a list of all agencies.
        Called via GET only.
    """
    
    # Validate our method
    if request.method != 'GET':
        return method_not_allowed('GET only!')
        
    return render_to_json([agency.to_jsonable() for agency in Agency.all()])
    
def api_agencies_search(request):
    """
        Return a list of agencies that match the search criterion.
        Called via GET only.
        
        paramters:
            type        ["location", "city", "state", "all"]
            lat,lon     (if location)
            city/state  (if city/state. If city, you must also include state)
        returns:
            a json list of agencies (using to_jsonable)         
    """
    
    # Validate our method
    if request.method != 'GET':
        return method_not_allowed('GET only!')
    
    # Validate our search type
    search_type = request.GET.get('type', None)
    if search_type not in ['location', 'city', 'state', 'all']:
        return bad_request('type parameter must be "location", "city", "state", or "all"')
        
    if search_type == 'location':
        # validate latitude and longitude
        try:
            latitude = float(request.GET.get('lat', None))
            longitude = float(request.GET.get('lon', None))
        except:
            return bad_request('lat/lon parameters must be supplied and must be valid floats')
        if not are_latitude_and_longitude_valid(latitude, longitude):
            return bad_request('lat/lon parameters must be properly bounded')
        
        agencies_iter = Agency.fetch_agencies_near(latitude, longitude)
    else:
        agencies_iter = Agency.all()
                
        if search_type == 'city':
            city = request.GET.get('city', None)
            if not city:
                return bad_request('city parameter must be supplied')
            # Use slugs rather than raw city name to ensure matches regardless of caps, etc.
            agencies_iter = agencies_iter.filter('cityslug =', slugify(city))
        
        if search_type == 'city' or search_type == 'state':
            state = request.GET.get('state', None)
            if not state:
                return bad_request('state parameter must be supplied')
            # Use slugs rather than raw city name to ensure matches regardless of caps, etc.        
            agencies_iter = agencies_iter.filter('stateslug =', slugify(state))
    
    return render_to_json([agency.to_jsonable() for agency in agencies_iter])

def api_apps_all(request):
    """
        Return a list of all transit apps.
        Called via GET only.
    """

    # Validate our method
    if request.method != 'GET':
        return method_not_allowed('GET only!')

    return render_to_json([transit_app.to_jsonable() for transit_app in TransitApp.all()])

def api_apps_search(request):
    """
        Return a list of transit apps that match the search criterion.
        Called via GET only.
    
        paramters:
            lat,lon     (required)
            country     (required, country code 2-letter)
        returns:
            a json list of agencies (using to_jsonable)         
    """
    
    # Validate our method
    if request.method != 'GET':
        return method_not_allowed('GET only!')
    
    # Validate input
    try:
        latitude = float(request.GET.get('lat', None))
        longitude = float(request.GET.get('lon', None))
    except:
        return bad_request('lat/lon parameters must be supplied and must be valid floats')
    if not are_latitude_and_longitude_valid(latitude, longitude):
        return bad_request('lat/lon parameters must be properly bounded')
    
    country_code = request.GET.get('country')
    if not country_code:
        return bad_request('country parameter must be supplied')
    country_code = country_code.strip().upper()
    if len(country_code) != 2:
        return bad_request('country parameter must be two characters')
    
    # Query and render JSON!
    return render_to_json([transit_app.to_jsonable() for transit_app in TransitApp.iter_for_location_and_country_code(latitude, longitude, country_code)])

@requires_valid_agency_key_encoded
def api_apps_for_agency(request, agency):
    """
        Return a list of transit apps that support the given agency.
        Called via GET only.
    """
    
    # Validate our method
    if request.method != 'GET':
        return method_not_allowed('GET only!')
    
    return render_to_json([transit_app.to_jsonable() for transit_app in TransitApp.iter_for_agency(agency)])
    
@requires_valid_transit_app_slug
def api_agencies_for_app(request, transit_app):
    """
        Return a list of agencies that support the given transit app.
        Called via GET only.
    """

    # Validate our method
    if request.method != 'GET':
        return method_not_allowed('GET only!')
    
    return render_to_json([agency.to_jsonable() for agency in Agency.iter_for_transit_app(transit_app)])

def api_apps_for_agencies(request):
    """
        Return a list of transit apps that support the given agency.
        Called via GET only.
        
        parameters:
            key_encoded     [multiple, max 50]
    """

    # Validate our method
    if request.method != 'GET':
        return method_not_allowed('GET only!')
        
    # Validate our input (mostly)
    potential_keys = request.GET.getlist("key_encoded")
    if not potential_keys or (len(potential_keys) > 50):
        return bad_request('Too many keys.')
    
    # Turn input into real keys
    agency_keys = []
    for potential_key in potential_keys:
        try:
            agency_keys.append(db.Key(potential_key))
        except:
            return bad_request('At least one invalid agency key.')
    
    # Turn keys into real agencies
    try:
        agencies = Agency.get(agency_keys)
    except:
        return bad_request('At least one invalid agency key.')

    # Send off the apps!
    return render_to_json([transit_app.to_jsonable() for transit_app in TransitApp.iter_for_agencies(agencies)])


def api_agencies_for_apps(request):
    """
        Return a list of agencies that support the given transit app.
        Called via GET only.
        
        parameters:
            transit_app_slug    [multiple, max 50]
    """
    
    # Validate our method
    if request.method != 'GET':
        return method_not_allowed('GET only!')
        
    # Validate our input (mostly)
    potential_transit_app_slugs = request.GET.getlist("transit_app_slug")
    if not potential_transit_app_slugs or (len(potential_transit_app_slugs) > 50):
        return bad_request('Too many transit app slugs.')
        
    # Turn slugs into real transit apps
    transit_apps = []
    for potential_transit_app_slug in potential_transit_app_slugs:
        transit_app = TransitApp.transit_app_for_slug(potential_transit_app_slug)
        if not transit_app:
            return bad_request('At least one invalid transit app slug.')
        transit_apps.append(transit_app)
    
    # Send off the agencies
    return render_to_json([agency.to_jsonable() for agency in Agency.iter_for_transit_apps(transit_apps)])
