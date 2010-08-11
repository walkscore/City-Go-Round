import time
import logging
import pickle

from decimal import Decimal
from datetime import datetime, timedelta, date

from django.conf import settings
from django.http import Http404
from google.appengine.ext import db
from google.appengine.api import memcache

from ..forms import NewAppGeneralInfoForm, NewAppAgencyForm, NewAppLocationForm, PetitionForm, EditAppGeneralInfoForm, EditAppLocationForm, EditAppAgencyForm, EditAppImagesForm
from ..utils.view import render_to_response, redirect_to, not_implemented, render_image_response, redirect_to_url, method_not_allowed, render_to_json
from ..utils.prettyprint import pretty_print_price
from ..utils.progressuuid import add_progress_uuid_to_session, remove_progress_uuid_from_session
from ..utils.screenshot import kick_off_resizing_for_screen_shots, kick_off_resizing_for_screen_shot
from ..utils.misc import chunk_sequence, pad_list, collapse_list
from ..utils.ratings import get_user_rating_for_app, set_user_rating_for_app, adjust_rating_for_app
from ..utils.memcache import clear_all_apps
from ..utils.mailer import kick_off_new_app_notification
from ..decorators import requires_valid_transit_app_slug, requires_valid_progress_uuid, requires_POST, memcache_view_response, memcache_parameterized_view_response
from ..models import Agency, TransitApp, TransitAppStats, TransitAppLocation, TransitAppFormProgress, FeedReference, NamedStat

from django.http import HttpResponse, HttpResponseForbidden
from django.utils import simplejson as json

def nearby(request):
    petition_form = PetitionForm()
    location_query = request.GET.get('q','')
    template_vars = {
        'petition_form': petition_form,
        'location_query': location_query
    }    
    return render_to_response(request, 'app/nearby.html', template_vars)

@memcache_view_response(time = settings.MEMCACHE_PAGE_SECONDS)
def gallery(request):

    def app_in_list(app, list):
        for item in list:
            if (app.slug == item.slug):
                return True
        return False
        
    NUM_RECENT_APPS = 3
    NUM_FEATURED_APPS = 3
    CATEGORIES = ["Public Transit", "Biking", "Walking", "Driving"]
    
    all_apps = TransitApp.fetch_all_sorted_by_rating()

    recent_list = TransitApp.all_by_most_recently_added().fetch(NUM_RECENT_APPS)
    featured_list = []
    # make dict of category_name:[]
    categorized_list = dict([(x,[]) for x in CATEGORIES])
    
    for app in all_apps:
        # if it's recently added, don't show it again
        if app_in_list(app, recent_list):
            continue
        
        # if it's featured, don't show it again
        if app.is_featured and len(featured_list) < NUM_FEATURED_APPS:
            featured_list.append(app)
            continue

        # if an app is in a category, add it to that category's list and then
        # break to prevent it from being added to any other category's list
        for category in CATEGORIES:
            if category in app.categories:
                categorized_list[category].append( app )
                
    template_vars = {
        'biking_apps':         categorized_list.get('Biking',[]),
        'walking_apps':        categorized_list.get('Walking',[]),
        'driving_apps':        categorized_list.get('Driving',[]),
        'transit_apps':        categorized_list.get('Public Transit',[]),
        'featured_apps':       featured_list, 
        'recently_added_apps': recent_list, 
        'transit_app_count':   TransitApp.query_all().count(),
        'public_feed_count':   Agency.all().filter("date_opened != ", None).count(),
    }
        
    return render_to_response(request, 'app/gallery.html', template_vars)
    
@requires_valid_transit_app_slug
def details(request, transit_app):
    rating_for_js = get_user_rating_for_app(request, transit_app)
    if rating_for_js is None:
        rating_for_js = 'null'
        
    template_vars = {
        'transit_app': transit_app,
        'formatted_price': pretty_print_price(transit_app.price),
        'explicit_agencies': [agency for agency in Agency.iter_explicitly_supported_for_transit_app(transit_app)],
        'supports_public_agencies': transit_app.supports_all_public_agencies,
        'current_user_rating': rating_for_js,
        'locations': transit_app.get_supported_location_list(),
    }    
    return render_to_response(request, 'app/details.html', template_vars)

@requires_valid_transit_app_slug
def app_location(request, transit_app):
        
    template_vars = {
        'transit_app': transit_app,
        'explicit_agencies': [agency for agency in Agency.iter_explicitly_supported_for_transit_app(transit_app)],
        'supports_public_agencies': transit_app.supports_all_public_agencies,
        'locations': transit_app.get_supported_location_list(),
        'location_query': request.GET.get('q',''),
    }    
    return render_to_response(request, 'app/location.html', template_vars)


@requires_valid_transit_app_slug
def screenshot(request, transit_app, screen_shot_index, screen_shot_size_name):
    # To make caching of images behave better when we update an app's images, use
    # families instead of indexes as part of the memcache key
    screen_shot_index = int(screen_shot_index)
    if screen_shot_index < transit_app.screen_shot_count:
        screen_shot_family = transit_app.screen_shot_families[screen_shot_index]
    else:
        screen_shot_family = "defaultfamily"
    
    memcache_key = "screenshot-%s-%s-%s" % (transit_app.slug, screen_shot_family, screen_shot_size_name)
    bytes = memcache.get(memcache_key)
    if bytes is None:
        bytes, ignored_extension = transit_app.get_screen_shot_bytes_and_extension(index = screen_shot_index, size_name = screen_shot_size_name)
        if not bytes:
            # Double check validity of size name -- for safety's sake
            if not screen_shot_size_name in [name for name, size in TransitApp.SCREEN_SHOT_SIZES]:
                raise Http404            
            default_image = open("%s-%s.png" % (settings.DEFAULT_TRANSIT_APP_BASE, screen_shot_size_name))
            bytes = default_image.read()
            default_image.close()
        if len(bytes) <= settings.MEMCACHE_SCREENSHOT_MAX_SIZE:
            memcache.set(memcache_key, bytes, time = settings.MEMCACHE_SCREENSHOT_SECONDS)    

    # NOTE/HACK: right now I just assume the extension is PNG (it's hard coded into the URL)    
    return render_image_response(request, bytes)

def add_form(request):
    if request.method == 'POST':
        form = NewAppGeneralInfoForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a data store entity to hold on to progress with our form
            progress = TransitAppFormProgress.new_with_uuid()
                        
            # Process the images, resizing if desired, and failing silently if something goes wrong.
            screen_shot_files = [request.FILES.get(name, None) for name in NewAppGeneralInfoForm.SCREEN_SHOT_FIELDS]
            screen_shot_files_bytes = [screen_shot_file.read() if screen_shot_file else None for screen_shot_file in screen_shot_files]
            families = kick_off_resizing_for_screen_shots(screen_shot_files_bytes)            
            progress.screen_shot_families.extend(families)
            
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
                "price": form.cleaned_data['price'],
            }
            progress.info_form_pickle = pickle.dumps(info_form, pickle.HIGHEST_PROTOCOL)
            
            # Save the form's progress to the AppEngine data store.
            # TODO error handling.
            progress.put()
            
            # Remember the current UUID in the session.
            add_progress_uuid_to_session(request, progress.progress_uuid)

            # Go to step 2. With fix of github.com/bmander/CityGoRound/issue #36, we go here always...
            return redirect_to("apps_add_agencies", progress_uuid = progress.progress_uuid)                
    else:
        form = NewAppGeneralInfoForm()        
    return render_to_response(request, 'app/add-form.html', {'form': form})
    
@requires_valid_progress_uuid
def add_agencies(request, progress_uuid):
    if request.method == "POST":
        form = NewAppAgencyForm(request.POST)
        if form.is_valid():
            agency_form = {
                "gtfs_choice": form.cleaned_data['gtfs_choice'],
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

    agency_list = Agency.fetch_all_agencies_as_jsonable()
    template_vars = {
        "form": form,
        "agencies": agency_list,
        "states": [x[1] for x in Agency.get_state_list()],
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
            transit_app.price = info_form['price']
            transit_app.author_name = info_form['author_name']
            transit_app.author_email = db.Email(info_form['author_email'])
            transit_app.long_description = info_form['long_description']
            transit_app.tags = info_form['tag_list']
            transit_app.platforms = info_form['platform_list']
            transit_app.categories = info_form['category_list']
            transit_app.screen_shot_families = progress.screen_shot_families
            transit_app.refresh_bayesian_average()
            
            # 2. Unpack and handle the agency form
            agency_form = pickle.loads(progress.agency_form_pickle)
            if agency_form["gtfs_choice"] == "nothing":
                transit_app.supports_any_gtfs = False
                transit_app.supports_all_public_agencies = False
            else:
                transit_app.supports_any_gtfs = True
                if agency_form["gtfs_choice"] == "public_agencies":
                    transit_app.supports_all_public_agencies = True
                elif agency_form["encoded_agency_keys"]:
                    transit_app.supports_all_public_agencies = False
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
                
            # Fire off a notification email
            kick_off_new_app_notification(transit_app)
            
            # Done with this particular progress UUID. Goodbye.
            remove_progress_uuid_from_session(request, progress_uuid)
            progress.delete()

            # Wow, we finished! 
            clear_all_apps()
            return redirect_to("apps_add_success")
    else:
        form = NewAppLocationForm(initial = {"progress_uuid": progress_uuid})
    
    # 2. Unpack the agency form to see if they selected agencies...
    progress = TransitAppFormProgress.get_with_uuid(progress_uuid)
    if progress and progress.agency_form_pickle:
        agency_form = pickle.loads(progress.agency_form_pickle)
        agencies_selected = (agency_form["gtfs_choice"] != "nothing")
    else:
        # this should happen in debug/local server only
        agencies_selected = False # for test purposes
    
    template_vars = {
        "form": form,
        "agencies_selected": agencies_selected,
    }
    return render_to_response(request, 'app/add-locations.html', template_vars)
        
def add_success(request):
    return render_to_response(request, 'app/add-success.html')

def admin_apps_list(request):
    return render_to_response(request, 'admin/apps-list.html')
    
@requires_valid_transit_app_slug
def admin_apps_edit(request, transit_app):
    return render_to_response(request, 'admin/app-edit.html', {'transit_app': transit_app})
    
@requires_valid_transit_app_slug
def admin_apps_edit_basic(request, transit_app):
    if request.method == "POST":
        form = EditAppGeneralInfoForm(request.POST, request.FILES)
        if form.is_valid():
            transit_app.title = form.cleaned_data["title"]
            transit_app.slug = form.transit_app_slug
            transit_app.description = form.cleaned_data["description"]
            transit_app.url = form.cleaned_data["url"]
            transit_app.price = form.cleaned_data["price"]
            transit_app.author_name = form.cleaned_data["author_name"]
            transit_app.author_email = form.cleaned_data["author_email"]
            transit_app.long_description = form.cleaned_data["long_description"]
            transit_app.platforms = form.platform_list
            transit_app.categories = form.category_list
            transit_app.tags = form.tag_list
            transit_app.is_featured = form.cleaned_data["is_featured"]
            transit_app.is_hidden = form.cleaned_data["is_hidden"]
            transit_app.put()    
                    
            clear_all_apps()
            return redirect_to("admin_apps_edit", transit_app_slug = transit_app.slug)
    else:
        form_initial_values = {
            "original_slug": transit_app.slug,
            "title": transit_app.title,
            "description": transit_app.description,
            "url": transit_app.url,
            "price": transit_app.price,
            "author_name": transit_app.author_name,
            "author_email": transit_app.author_email,
            "long_description": transit_app.long_description,
            "platforms": transit_app.platform_choice_list,
            "categories": transit_app.category_choice_list,
            "tags": transit_app.tag_list_as_string,
            "is_featured": transit_app.is_featured,
            "is_hidden": transit_app.is_hidden,
        }
        form = EditAppGeneralInfoForm(initial = form_initial_values)
    
    template_vars = {
        'form': form,
        'transit_app': transit_app,
    }
    return render_to_response(request, 'admin/app-edit-basic.html', template_vars)
    
@requires_valid_transit_app_slug
def admin_apps_edit_locations(request, transit_app):
    if request.method == "POST":
        form = EditAppLocationForm(request.POST)
        if form.is_valid():
            # 1. line up all TransitAppLocation instances that match this app...
            transit_app_locations_to_delete = [transit_app_location for transit_app_location in transit_app.explicitly_supported_locations]
            transit_app.explicitly_supported_countries = []   
            transit_app.explicitly_supported_city_slugs = []
            transit_app.explicitly_supported_city_details = []         
            
            # 2. Now deal with locations...
            transit_app.explicitly_supports_the_entire_world = form.cleaned_data["available_globally"]
            lazy_locations = transit_app.add_explicitly_supported_city_infos_lazy(form.cleaned_data["location_list"].unique_cities)
            transit_app.add_explicitly_supported_countries([country.country_code for country in form.cleaned_data["location_list"].unique_countries])
                        
            # Write the transit app to the data store, along with custom locations (if any)
            clear_all_apps()
            transit_app.put()

            if lazy_locations:
                real_locations = [lazy_location() for lazy_location in lazy_locations]
                db.put(real_locations)
            for chunk in chunk_sequence(transit_app_locations_to_delete, 10):
                db.delete(chunk)                
            return redirect_to("admin_apps_edit", transit_app_slug = transit_app.slug)
    else:
        form_initial_values = {
            "available_globally": transit_app.explicitly_supports_the_entire_world,
        }
        form = EditAppLocationForm(initial = form_initial_values)
        
    # Pull together an initial location string from cities...
    locations = []
    for transit_app_location in transit_app.explicitly_supported_locations:
        location_parts = [str(transit_app_location.location.lat), str(transit_app_location.location.lon)]            
        if transit_app_location.city_details:
            location_parts.append(transit_app_location.city_details)
        location = ','.join(location_parts)
        locations.append(location)
    
    # ...and from countries
    for explicitly_supported_country in transit_app.explicitly_supported_countries:
        locations.append(explicitly_supported_country)

    # Make it happy for the form. HAPPY, DAMMIT.
    location_list = '|'.join(locations)
                    
    template_vars = {
        'form': form,
        'transit_app': transit_app,
        'location_list': location_list,
    }
    return render_to_response(request, "admin/app-edit-locations.html", template_vars)
    
@requires_valid_transit_app_slug
def admin_apps_edit_agencies(request, transit_app):
    if request.method == "POST":
        form = EditAppAgencyForm(request.POST)
        if form.is_valid():
            transit_app.explicitly_supported_agency_keys = []
            if form.cleaned_data["gtfs_choice"] == "nothing":
                transit_app.supports_any_gtfs = False
                transit_app.supports_all_public_agencies = False
            else:
                transit_app.supports_any_gtfs = True
                if form.cleaned_data["gtfs_choice"] == "public_agencies":
                    transit_app.supports_all_public_agencies = True
                else:
                    transit_app.supports_all_public_agencies = False
                    transit_app.add_explicitly_supported_agencies(form.cleaned_data['agency_list'])

            clear_all_apps()
            transit_app.put()
            
            return redirect_to("admin_apps_edit", transit_app_slug = transit_app.slug)
    else:
        if transit_app.supports_any_gtfs:
            if transit_app.supports_all_public_agencies:
                gtfs_choice = "public_agencies"
            else:
                gtfs_choice = "specific_agencies"
        else:
            gtfs_choice = "nothing"            
        form_initial_values = {
            "gtfs_choice": gtfs_choice,
        }        
        form = EditAppAgencyForm(initial = form_initial_values)    
    
    agency_list = Agency.fetch_all_agencies_as_jsonable()
    template_vars = {
        'form': form,
        'transit_app': transit_app,
        'angency_keys_encoded': '|'.join([str(key) for key in transit_app.explicitly_supported_agency_keys]),
        "agencies": agency_list,
        "states": [x[1] for x in Agency.get_state_list()],
        "agency_count": len(agency_list),
    }
    return render_to_response(request, "admin/app-edit-agencies.html", template_vars)
    
@requires_valid_transit_app_slug
def admin_apps_edit_images(request, transit_app):
    too_few_error = ''
    
    if request.method == "POST":        
        form = EditAppImagesForm(request.POST, request.FILES)
        if form.is_valid():
            final_family_order = [screen_shot_family for screen_shot_family in transit_app.screen_shot_families]
            pad_list(final_family_order, EditAppImagesForm.SCREEN_SHOT_COUNT, pad_with = None)
            
            # Remove families we no longer need...
            for remove_family in form.cleaned_data['remove_list']:
                if remove_family in final_family_order:
                    final_family_order[final_family_order.index(remove_family)] = None
            
            # Process all new images, remembering their positions
            screen_shot_files = [request.FILES.get(name, None) for name in EditAppImagesForm.SCREEN_SHOT_FIELDS]
            screen_shot_files_bytes = [screen_shot_file.read() if screen_shot_file else None for screen_shot_file in screen_shot_files]
            for i, screen_shot_file_bytes in enumerate(screen_shot_files_bytes):
                if screen_shot_file_bytes:
                    family = kick_off_resizing_for_screen_shot(screen_shot_file_bytes)
                    if family is not None:
                        final_family_order[i] = family
            
            # Now collapse down the list by removing empty screen shot slots
            collapse_list(final_family_order)
            
            # Sanity check before writing...                    
            if len(final_family_order) == 0:
                too_few_error = "*** There were too few images after removing. All apps must have at least one image. Try again."
                transit_app = TransitApp.transit_app_for_slug(transit_app.slug)
            else:
                # Finally, write the transit app and blobs
                # TODO error handling.
                transit_app.screen_shot_families = final_family_order
                transit_app.put()
                return redirect_to("admin_apps_edit", transit_app_slug = transit_app.slug)            
    else:
        form = EditAppImagesForm()
        
    template_vars = {
        'form': form,
        'transit_app': transit_app,
        'screen_shots_json': json.dumps(transit_app.screen_shots_to_jsonable()),
        'too_few_error': too_few_error,
    }
    return render_to_response(request, "admin/app-edit-images.html", template_vars)
        
@requires_POST
@requires_valid_transit_app_slug
def admin_apps_delete(request, transit_app):
    try:
        # Get rid of all associated TransitAppLocation instances
        locations = [explicitly_supported_location for explicitly_supported_location in transit_app.explicitly_supported_locations]
        for location_chunk in chunk_sequence(locations, 5):
            db.delete(location_chunk)
            
        # Get rid of the transit app itself.
        clear_all_apps()
        transit_app.delete()        
    except Exception:
        return render_to_json({"success": False, "transit_app_slug": transit_app.slug})
    return render_to_json({"success": True, "transit_app_slug": transit_app.slug})
        
@requires_POST
@requires_valid_transit_app_slug
def admin_apps_hide_unhide(request, transit_app):
    try:
        transit_app.is_hidden = not transit_app.is_hidden
        transit_app.put()
    except Exception:
        return render_to_json({"success": False, "transit_app_slug": transit_app.slug})
    return render_to_json({"success": True, "transit_app_slug": transit_app.slug, "is_hidden": transit_app.is_hidden})
        
def increment_stat(request):
    stat_name = request.GET['name']
    stat_value = NamedStat.increment( stat_name )
    return HttpResponse( "the new value of %s is %s"%(stat_name,stat_value) )

@requires_POST
@requires_valid_transit_app_slug
def app_rating_vote(request, transit_app):
    # Get our input
    new_rating = request.POST.get('rating', None)
    
    # Validate that it is a number (or is missing)
    if new_rating is not None:
        try:
            new_rating = int(new_rating)
        except (TypeError, ValueError):
            return bad_request("Invalid rating: not a number.")

    # Validate that it is "in range"
    if (new_rating is not None) and ((new_rating < 0) or (new_rating > 5)):
        return bad_request("Invalid rating: out of range.")

    # Update the rating
    old_rating = get_user_rating_for_app(request, transit_app)
    adjust_rating_for_app(transit_app, old_rating, new_rating)
    set_user_rating_for_app(request, transit_app, new_rating)

    # Done!
    return render_to_json([transit_app.average_rating, transit_app.num_ratings])
    
def refresh_all_bayesian_averages(request):
    all_apps = TransitApp.query_all(visible_only = False)
    
    all_rating_sum = NamedStat.get_stat( "all_rating_sum" )
    all_rating_count = NamedStat.get_stat( "all_rating_count" )
    
    for app in all_apps:
        logging.info( "%s: old bayesian average %s"%(app.key().id(), app.bayesian_average) )
        app.refresh_bayesian_average( all_rating_sum, all_rating_count )
        app.put()
        logging.info( "%s: new bayesian average %s"%(app.key().id(), app.bayesian_average) )
        
    return HttpResponse( "Should have worked alright. Check out the log." )
    
def admin_apps_update_schema(request):
    changed_apps = []
    new_families = []

    for transit_app in TransitApp.query_all(visible_only = False):    
        changed = False
        
        # Make sure that the app has appropriate dates
        if not transit_app.date_added:
            transit_app.date_added = datetime.now()
            changed = True
            
        if not transit_app.date_last_updated:
            transit_app.date_last_updated = datetime.now()
            changed = True
            
        if not transit_app.is_featured:
            transit_app.is_featured = False
            changed = True
        
        if not transit_app.supports_any_gtfs:
            transit_app.supports_any_gtfs = False
            changed = True
            
        if not transit_app.supports_all_public_agencies:
            transit_app.supports_all_public_agencies = False
            changed = True
        
        if not transit_app.explicitly_supports_the_entire_world:
            transit_app.explicitly_supports_the_entire_world = False
            changed = True
            
        if not transit_app.price:
            transit_app.price = Decimal("0.00")
            changed = True
            
        if not transit_app.is_hidden:
            transit_app.is_hidden = False
            changed = True
            
        blob = transit_app.screen_shot
        if blob:
            changed = True
            transit_app.screen_shot = None
            
            # Oh boy. We have to make screen shots.
            if not transit_app.screen_shot_families:
                transit_app.screen_shot_families = []                
            families = kick_off_resizing_for_screen_shots([str(blob)])                
            transit_app.screen_shot_families.extend(families)
            new_families = []
            
        # Remember this app, if it changed
        if changed:
            changed_apps.append(transit_app)
    
    # Looks like we're done. Attempt to commit everything to our database.
    for changed_app_chunk in chunk_sequence(changed_apps, 10):
        db.put(changed_app_chunk)
    
    # Render some vaguely useful results
    template_vars = {
        "update_count": len(changed_apps),
        "family_count": len(new_families),
    }    
    return render_to_response(request, "admin/apps-update-schema-finished.html", template_vars)
