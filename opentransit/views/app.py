import time
import logging
import pickle

from django.conf import settings
from google.appengine.ext import db

from ..forms import NewAppGeneralInfoForm, NewAppAgencyForm, NewAppLocationForm, PetitionForm
from ..utils.view import render_to_response, redirect_to, not_implemented, render_image_response, redirect_to_url
from ..utils.image import crop_and_resize_image_to_square
from ..decorators import requires_valid_transit_app_slug
from ..models import TransitApp, TransitAppStats, TransitAppLocation, TransitAppFormProgress

def nearby(request):
    petition_form = PetitionForm()    
    template_vars = {
        'petition_form': petition_form
    }    
    return render_to_response(request, 'app/nearby.html', template_vars)

def gallery(request):    
    template_vars = {
        'transit_app_count': TransitAppStats.get_transit_app_count(),
        'transit_apps': TransitApp.all().fetch(10), # TODO DAVEPECK: replace with something better
    }
        
    return render_to_response(request, 'app/gallery.html', template_vars)
    
@requires_valid_transit_app_slug
def details(request, transit_app):
    template_vars = {
        'transit_app': transit_app,
    }    
    return render_to_response(request, 'app/details.html', template_vars)
    
@requires_valid_transit_app_slug
def screenshot(request, transit_app):
    if transit_app.has_screen_shot:
        return render_image_response(request, transit_app.screen_shot)
    return redirect_to_url("/images/default-transit-app.png")

def add_form(request):
    # TODO davepeck
    if request.method == 'POST':
        form = NewAppGeneralInfoForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a data store entity to hold on to progress with our form
            form_progress = TransitAppFormProgress.new_with_uuid()
                        
            # Process the image, resizing if necessary, and failing silently if something goes wrong.
            screen_shot_file = request.FILES.get('screen_shot', None)
            if screen_shot_file:
                screen_shot_bytes = crop_and_resize_image_to_square(screen_shot_file.read(), settings.TRANSIT_APP_IMAGE_WIDTH, settings.TRANSIT_APP_IMAGE_HEIGHT)
                if screen_shot_bytes:
                    form_progress.screen_shot = db.Blob(screen_shot_bytes)

            # Hold onto the information in this form, so we can use it later.
            # (Unfortunately we can't just pickle the form itself.)
            info_form = {
                "title": form.cleaned_data['title'],
                "description": form.cleaned_data['description'],
                "url": form.cleaned_data['url'],
                "author_name": form.cleaned_data['author_name'],
                "author_email": form.cleaned_data['author_email'],
                "long_description": form.cleaned_data['long_description'],
                "platforms": form.cleaned_data['platforms'],
                "categories": form.cleaned_data['categories'],
                "tags": form.cleaned_data['tags'],
                "gtfs_choice": form.cleaned_data['gtfs_choice'],
            }
            form_progress.info_form_pickle = pickle.dumps(info_form, pickle.HIGHEST_PROTOCOL)
            
            # Save the form's progress to the AppEngine data store.
            form_progress.put()
            
            # Remember the current UUID in the session. The user may be
            # working on multiple forms at once, so hold on to a list.
            progress_uuids = request.get_session("progress_uuids", [])
            progress_uuids.append(form_progress.progress_uuid)
            request.set_session("progress_uuids", progress_uuids)
            
            # Redirect to the appropriate next page, based on whether 
            # they want to associate with agencies, or just associate 
            # with cities and countries.
            if form.cleaned_data["gtfs_choice"] == "yes_gtfs":
                return redirect_to("apps_add_agencies", progress_uuid = form_progress.progress_uuid)
            else:
                return redirect_to("apps_and_locations", progress_uuid = form_progress.progress_uuid)                    
    else:
        form = NewAppGeneralInfoForm()        
    return render_to_response(request, 'app/add-form.html', {'form': form})
    
def add_locations(request, progress_uuid):
    return render_to_response(request, 'app/add-locations.html')
    
def add_agencies(request, progress_uuid):
    return render_to_response(request, 'app/add-agencies.html')
    
def add_success(request):
    return render_to_response(request, 'app/add-success.html')

