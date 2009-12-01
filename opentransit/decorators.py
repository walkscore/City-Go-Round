from django.http import Http404, HttpResponseForbidden
from google.appengine.ext import db
from google.appengine.api import users
from .models import TransitApp, Agency
from .utils.httpbasicauth import authenticate_request
from .utils.progressuuid import is_progress_uuid_valid
from .utils.view import method_not_allowed

def requires_method(view_function, method):
    def wrapper(request, *args, **kwargs):
        if request.method != method:
            return method_not_allowed("Must be called with %s." % method)
        return view_function(request, *args, **kwargs)
    return wrapper

def requires_GET(view_function):
    return requires_method(view_function, method = "GET")
    
def requires_POST(view_function):
    return requires_method(view_function, method = "POST")
    
def requires_http_basic_authentication(view_function, correct_username, correct_password, realm = None):
    def wrapper(request, *args, **kwargs):
        authentication_response = authenticate_request(request, correct_username, correct_password, realm)
        if authentication_response is not None:
            return authentication_response
        return view_function(request, *args, **kwargs)   
    return wrapper     

def requires_valid_transit_app_slug(view_function):
    def wrapper(request, transit_app_slug, *args, **kwargs):
        transit_app = TransitApp.transit_app_for_slug(transit_app_slug)
        if transit_app is not None:
            return view_function(request, transit_app, *args, **kwargs)
        else:
            raise Http404
    return wrapper
    
def requires_valid_progress_uuid(view_function):
    def wrapper(request, progress_uuid, *args, **kwargs):
        if not is_progress_uuid_valid(request, progress_uuid):
            raise Http404
        return view_function(request, progress_uuid, *args, **kwargs)
    return wrapper
    
def requires_valid_agency_key_encoded(view_function):
    def wrapper(request, key_encoded, *args, **kwargs):
        try:
            agency = Agency.get(db.Key(key_encoded.strip()))
        except:
            raise Http404
        return view_function(request, agency, *args, **kwargs)
    return wrapper

def requires_google_admin_login(view_function):
    def wrapper(request, *args, **kwargs):
        if not users.is_current_user_admin():
            return HttpResponseForbidden()
        else:
            return view_function(request, *args, **kwargs)
    return wrapper
