import time
import logging
import pickle

from datetime import datetime, timedelta, date

from django.conf import settings
from google.appengine.ext import db

from ..forms import NewAppGeneralInfoForm, NewAppAgencyForm, NewAppLocationForm, PetitionForm
from ..utils.view import render_to_response, redirect_to, not_implemented, render_image_response, redirect_to_url
from ..utils.image import crop_and_resize_image_to_square
from ..utils.progressuuid import add_progress_uuid_to_session, remove_progress_uuid_from_session
from ..decorators import requires_valid_transit_app_slug, requires_valid_progress_uuid
from ..models import Agency, TransitApp, TransitAppStats, TransitAppLocation, TransitAppFormProgress, FeedReference

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
        'transit_apps': TransitApp.all().fetch(40), # TODO DAVEPECK: fix these queries
        'featured_apps': TransitApp.all().fetch(3), 
        'recently_added_apps': TransitApp.all().fetch(3), 
        'transit_app_count': TransitApp.all().count(),
        'public_feed_count': Agency.all().filter("date_opened != ", None).count(),
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
                "supports_gtfs": form.cleaned_data['supports_gtfs'],
            }
            progress.info_form_pickle = pickle.dumps(info_form, pickle.HIGHEST_PROTOCOL)
            
            # Save the form's progress to the AppEngine data store.
            # TODO error handling.
            progress.put()
            
            # Remember the current UUID in the session.
            add_progress_uuid_to_session(request, progress.progress_uuid)
            
            # Redirect to the appropriate next page, based on whether 
            # they want to associate with agencies, or just associate 
            # with cities and countries.
            if form.cleaned_data["supports_gtfs"]:
                return redirect_to("apps_add_agencies", progress_uuid = progress.progress_uuid)                
            else:
                return redirect_to("apps_add_locations", progress_uuid = progress.progress_uuid)                    
    else:
        form = NewAppGeneralInfoForm()        
    return render_to_response(request, 'app/add-form.html', {'form': form})
    
@requires_valid_progress_uuid
def add_agencies(request, progress_uuid):
    if request.method == "POST":
        form = NewAppAgencyForm(request.POST)
        if form.is_valid():
            agency_form = {
                "gtfs_public_choice": form.cleaned_data['gtfs_public_choice'],
                "encoded_agency_keys": [str(agency_key) for agency_key in form.cleaned_data['agency_list']],
            }
            
            # Remember the form info as filled out.
            progress = TransitAppFormProgress.get_with_uuid(progress_uuid)
            progress.agency_form_pickle = pickle.dumps(agency_form, pickle.HIGHEST_PROTOCOL)
            progress.put()

            # Head to our last page...
            return redirect_to("apps_add_locations", progress_uuid = progress.progress_uuid)
    else:
        form = NewAppAgencyForm(initial = {"progress_uuid": progress_uuid})        

    #get agency list
    agency_list = Agency.fetch_for_slugs()
    template_vars = {
        "form": form,
        "agencies": agency_list,
        "states": Agency.get_state_list(),
        "agency_count": len(agency_list)
    }

    return render_to_response(request, 'app/add-agencies.html', template_vars)
    
@requires_valid_progress_uuid
def add_locations(request, progress_uuid):
    if request.method == "POST":
        form = NewAppLocationForm(request.POST)
        if form.is_valid():
            # Get all the progress so far.
            progress = TransitAppFormProgress.get_with_uuid(progress_uuid)
            
            # 1. Unpack and handle our general info form
            # TODO davepeck: it is possible that, in the interim, someone
            # finished making a transit_app with the same title...
            info_form = pickle.loads(progress.info_form_pickle)

            transit_app = TransitApp(title = info_form['title'])
            transit_app.description = info_form['description']
            transit_app.url = db.Link(info_form['url'])
            transit_app.author_name = info_form['author_name']
            transit_app.author_email = db.Email(info_form['author_email'])
            transit_app.long_description = info_form['long_description']
            transit_app.tags = info_form['tag_list']
            transit_app.platforms = info_form['platform_list']
            transit_app.categories = info_form['category_list']
            transit_app.supports_any_gtfs = info_form['supports_gtfs']
            transit_app.screen_shot = db.Blob(progress.screen_shot)
            
            # 2. If present, unpack and handle the agency form
            if progress.agency_form_pickle and str(progress.agency_form_pickle):
                agency_form = pickle.loads(progress.agency_form_pickle)
                if agency_form["gtfs_public_choice"] == "yes_public":
                    transit_app.supports_all_public_agencies = True
                elif agency_form["encoded_agency_keys"]:
                    transit_app.add_explicitly_supported_agencies([db.Key(encoded_agency_key) for encoded_agency_key in agency_form["encoded_agency_keys"]])
            
            # 3. Now handle the locations form (that's this form!)
            transit_app.explicitly_supports_the_entire_world = form.cleaned_data["available_globally"]
            lazy_locations = transit_app.add_explicitly_supported_city_infos_lazy(form.cleaned_data["location_list"].unique_cities)
            transit_app.add_explicitly_supported_countries([country.country_code for country in form.cleaned_data["location_list"].unique_countries])
            
            # Write the transit app to the data store, along with custom locations (if any)
            transit_app.put()
            if lazy_locations:
                real_locations = [lazy_location() for lazy_location in lazy_locations]
                db.put(real_locations)
            
            # Done with this particular progress UUID. Goodbye.
            remove_progress_uuid_from_session(request, progress_uuid)
            progress.delete()

            # Wow, we finished!
            return redirect_to("apps_add_success")
    else:
        form = NewAppLocationForm(initial = {"progress_uuid": progress_uuid})
    
    template_vars = {
        "form": form,
    }
    return render_to_response(request, 'app/add-locations.html', template_vars)
        
def add_success(request):
    return render_to_response(request, 'app/add-success.html')


def admin_apps_list(request):
    # TODO DAVEPECK
    return not_implemented(request)
    
def admin_apps_edit(request):
    # TODO DAVEPECK
    return not_implemented(request)
