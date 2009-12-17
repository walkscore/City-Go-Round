import logging

from ..forms import NewAppGeneralInfoForm, NewAppAgencyForm, NewAppLocationForm, PetitionForm, EditAppGeneralInfoForm, EditAppLocationForm, EditAppAgencyForm, EditAppImagesForm
from ..decorators import requires_POST
from ..utils.view import render_to_json
from ..utils.screenshot import create_and_store_screen_shot_blob_for_family
from ..utils.mailer import send_to_contact

from django.conf import settings

@requires_POST
def taskqueue_screen_shot_resize(request):
    family = request.POST.get('family', None)
    width_str = request.POST.get('width', None)
    height_str = request.POST.get('height', None)
    
    # Sanity check -- but should really never happen if we enqueue our tasks correctly...
    if (family is None) or (width_str is None) or (height_str is None):
        raise Error("Invalid screen shot resize task invocation.")
        
    # More... -- but should really never happen if we enqueue our tasks correctly...
    try:
        width = int(width_str)
        height = int(height_str)
    except (TypeError, ValueError):
        raise Error("Invalid width or height given to screen shot resize task invocation.")
    
    # Do the real work, and throw an exception if bad things happen.
    create_and_store_screen_shot_blob_for_family(family, width, height)
    
    # Done. HTTP 200 is all AppEngine needs to be happy.    
    return render_to_json({"success": True})
    
from django.http import HttpResponse
#@requires_POST
def taskqueue_notify_new_app(request):
    
    # get params from post
    app_id = request.POST.get('id', None)
    title = request.POST.get('title', None)
    app_url = request.POST.get('url', None)
    
    # do real work
    send_to_contact( "New CityGoRound.org App: \"%s\""%title, "There is a new CityGoRound.org App \"%s\" (id:%s) at %s. Could you check to make sure it isn't spam? Thanks."%(title, app_id, app_url), recipient=settings.NEW_APP_EMAIL_RECIPIENTS )
    
    # Done. HTTP 200 is all AppEngine needs to be happy.   
    return render_to_json({"success": True})
    