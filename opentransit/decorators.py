from django.http import Http404
from .models import TransitApp
from .utils.httpbasicauth import authenticate_request

def requires_http_basic_authentication(view_function, correct_username, correct_password, realm = None):
    def wrapper(request, *args, **kwargs):
        authentication_response = authenticate_request(request, correct_username, correct_password, realm)
        if authentication_response is not None:
            return authentication_response
        return view_function(request, *args, **kwargs)        

def requires_valid_transit_app_slug(view_function):
    def wrapper(request, transit_app_slug, *args, **kwargs):
        transit_app = TransitApp.transit_app_for_slug(transit_app_slug)
        if transit_app is not None:
            return view_function(request, transit_app, *args, **kwargs)
        else:
            raise Http404
    return wrapper