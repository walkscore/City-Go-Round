import time
import logging
import pickle

from django.conf import settings
from google.appengine.ext import db

from ..forms import NewAppGeneralInfoForm, NewAppAgencyForm, NewAppLocationForm, PetitionForm
from ..utils.view import render_to_response, redirect_to, not_implemented, render_image_response, redirect_to_url
from ..utils.image import crop_and_resize_image_to_square
from ..utils.progressuuid import add_progress_uuid_to_session, remove_progress_uuid_from_session
from ..decorators import requires_valid_transit_app_slug, requires_valid_progress_uuid
from ..models import TransitApp, TransitAppStats, TransitAppLocation, TransitAppFormProgress

def nearby(request):
    petition_form = PetitionForm()
    location_query = request.GET.get('location_query','')
    template_vars = {
        'petition_form': petition_form,
        'location_query': location_query
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
    if request.method == 'POST':
        form = NewAppGeneralInfoForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a data store entity to hold on to progress with our form
            progress = TransitAppFormProgress.new_with_uuid()
                        
            # Process the image, resizing if necessary, and failing silently if something goes wrong.
            screen_shot_file = request.FILES.get('screen_shot', None)
            if screen_shot_file:
                screen_shot_bytes = crop_and_resize_image_to_square(screen_shot_file.read(), settings.TRANSIT_APP_IMAGE_WIDTH, settings.TRANSIT_APP_IMAGE_HEIGHT)
                if screen_shot_bytes:
                    progress.screen_shot = db.Blob(screen_shot_bytes)

            # Hold onto the information in this form, so we can use it later.
            # (Unfortunately we can't just pickle the form itself.)
            info_form = {
                "title": form.cleaned_data['title'],
                "description": form.cleaned_data['description'],
                "url": form.cleaned_data['url'],
                "author_name": form.cleaned_data['author_name'],
                "author_email": form.cleaned_data['author_email'],
                "long_description": form.cleaned_data['long_description'],
                "platform_list": form.platform_list,
                "category_list": form.category_list,
                "tag_list": form.tag_list,
                "gtfs_choice": form.cleaned_data['gtfs_choice'],
            }
            progress.info_form_pickle = pickle.dumps(info_form, pickle.HIGHEST_PROTOCOL)
            
            # Save the form's progress to the AppEngine data store.
            progress.put()
            
            # Remember the current UUID in the session.
            add_progress_uuid_to_Session(progress.progress_uuid)
            
            # Redirect to the appropriate next page, based on whether 
            # they want to associate with agencies, or just associate 
            # with cities and countries.
            if form.cleaned_data["gtfs_choice"] == "yes_gtfs":
                return redirect_to("apps_add_agencies", progress_uuid = progress.progress_uuid)
            else:
                return redirect_to("apps_add_locations", progress_uuid = progress.progress_uuid)                    
    else:
        form = NewAppGeneralInfoForm()        
    return render_to_response(request, 'app/add-form.html', {'form': form})
    
def _process_and_remove_progress(progress_uuid):
    progress = TransitAppFormProgress.get_with_uuid(progress_uuid)
    info_form = pickle.loads(progress.info_form_pickle)
    # TODO davepeck: it is possible that, in the interim, someone
    # finished making a transit_app with the same title...
    transit_app = TransitApp(title = info_form['title'])
    transit_app.description = info_form['description']
    transit_app.url = db.Link(info_form['url'])
    transit_app.author_name = info_form['author_name']
    transit_app.author_email = db.Email(author_email)
    transit_app.long_description = info_form['long_description']
    transit_app.tags = info_form['tag_list']
    transit_app.platforms = info_form['platform_list']
    transit_app.categories = info_form['category_list']
    return transit_app
    
@requires_valid_progress_uuid
def add_locations(request, progress_uuid):
    if request.method == "POST":
        form = NewAppLocationForm(request.POST)
        if form.is_valid():
            # TODO davepeck: process this ish!
            return redirect_to("apps_add_success")
    else:
        form = NewAppLocationForm(initial = {"progress_uuid": progress_uuid})
    
    template_vars = {
        "form": form,
    }
    return render_to_response(request, 'app/add-locations.html', template_vars)
    
@requires_valid_progress_uuid
def add_agencies(request, progress_uuid):
    if request.method == "POST":
        form = NewAppAgencyForm(request.POST)
        if form.is_valid():
            # TODO davepeck: process this ish!
            return redirect_to("apps_add_success")
    else:
        form = NewAppAgencyForm(initial = {"progress_uuid": progress_uuid})
    
    template_vars = {
        "form": form,
    }
    return render_to_response(request, 'app/add-agencies.html', template_vars)
    
def add_success(request):
    return render_to_response(request, 'app/add-success.html')

