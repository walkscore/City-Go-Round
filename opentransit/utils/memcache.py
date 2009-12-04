from google.appengine.api import memcache

def key_for_view_function(view_function):    
    return "view_function-%s.%s" % (str(view_function.__module__), str(view_function.__name__))

def key_for_request(request):
    """Given a django HttpRequest, return a string that will be the same for same requests (URL, method, and parameters)"""
    params_string = "None"
    if request.method == "GET" or request.method == "POST":
        params = []
        query = request.GET if request.method == "GET" else request.POST
        for k, v_list in query.iterlists():
            for v in v_list:
                params.append("%s=%s" % (str(k), str(v)))
        params.sort()
        params_string = '-'.join(params)
    
    key = "request-%s-%s-%s" % (request.path, request.method, params_string)
    return key

def clear_for_view_function(view_function):
    memcache.delete(key_for_view_function(view_function))

def clear_for_request(request):
    memcache.delete(key_for_request(request))

def clear_app_gallery():
    from ..views.app import gallery as _gallery
    memcache.delete(key_for_view_function(_gallery))

def clear_api_apps_all():
    from ..views.api import api_apps_all as _api_apps_all
    memcache.delete(key_for_view_function(_api_apps_all))

def clear_all_apps():
    clear_app_gallery()
    clear_api_apps_all()

