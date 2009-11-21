import time
import logging

from django.http import HttpResponse, HttpResponseRedirect

from google.appengine.ext import db
from google.appengine.api import memcache

from ..models import Agency
from ..utils.view import render_to_response, redirect_to, not_implemented, bad_request, render_to_json
from ..utils.slug import slugify
from ..utils.geohelpers import are_latitude_and_longitude_valid

def api_search_agencies(request):
    """
        paramters:
            type        ["location", "city", "state"]
            lat,lon     (if location)
            city/state  (if city/state. If city, you must also include state)
        returns:
            a json list of agencies (using to_jsonable)         
    """
    
    # Validate our search type
    search_type = request.GET.get('type', None)
    if search_type not in ['location', 'city', 'state']:
        return bad_request('type parameter must be "location", "city", or "state"')
        
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
        
        state = request.GET.get('state', None)
        if not state:
            return bad_request('state parameter must be supplied')
        # Use slugs rather than raw city name to ensure matches regardless of caps, etc.        
        agencies_iter = agencies_iter.filter('stateslug =', slugify(state))
    
    return render_to_json([agency.to_jsonable() for agency in agencies_iter])

def api_search_apps(request):
    """
        paramters:
            lat,lon     (required)
            country     (required, country code 2-letter)
        returns:
            a json list of agencies (using to_jsonable)         
    """
    
    # 0. Validate input
    try:
        latitude = float(request.GET.get('lat', None))
        longitude = float(request.GET.get('lon', None))
    except:
        return bad_request('lat/lon parameters must be supplied and must be valid floats')
    if not are_latitude_and_longitude_valid(latitude, longitude):
        return bad_request('lat/lon parameters must be properly bounded')
    
    country_code_x = request.GET.get('country')
    if not country_code_x:
        return bad_request('country parameter must be supplied')
    country_code = country_code_x.strip().upper()
    if len(country_code) != 2:
        return bad_request('country parameter must be two characters')
    
    return render_to_json([transit_app.to_jsonable() for transit_app in TransitApp.iter_for_location(latitude, longitude, country_code)])
