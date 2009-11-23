import time
import logging
 
from django.http import HttpResponse, HttpResponseRedirect
 
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
 
from ..forms import AgencyForm
from ..models import Agency, FeedReference, TransitApp
from ..utils.view import render_to_response, redirect_to, not_implemented, bad_request, render_to_json
from ..utils.misc import uniquify, chunk_sequence
from ..utils.geocode import geocode_name
 
from StringIO import StringIO
import csv

def edit_agency(request, agency_id=None):
    if agency_id is not None:
        agency = Agency.get_by_id( int(agency_id) )
    else:
        agency = None
    
    if request.method == 'POST':
        
        form = AgencyForm(request.POST)
        if form.is_valid():
            if agency is None:
                agency = Agency(name=form.cleaned_data['name'],
                                city=form.cleaned_data['city'],
                                state=form.cleaned_data['state'],
                                country=form.cleaned_data['country'])
            
            agency.name       = form.cleaned_data['name']
            agency.short_name = form.cleaned_data['short_name']
            agency.city       = form.cleaned_data['city']
            agency.state      = form.cleaned_data['state']
            agency.country    = form.cleaned_data['country'] if form.cleaned_data['country'] != "" else None
            agency.postal_code      = form.cleaned_data['postal_code']
            agency.address          = form.cleaned_data['address']
            agency.agency_url       = form.cleaned_data['agency_url'] if form.cleaned_data['agency_url'] != "" else None
            agency.executive        = form.cleaned_data['executive']
            agency.executive_email  = form.cleaned_data['executive_email'] if form.cleaned_data['executive_email'] != "" else None
            agency.twitter          = form.cleaned_data['twitter']
            agency.contact_email    = form.cleaned_data['contact_email'] if form.cleaned_data['contact_email'] != "" else None
            agency.updated          = form.cleaned_data['updated']
            agency.phone            = form.cleaned_data['phone']
            agency.gtfs_data_exchange_id      = form.cleaned_data['gtfs_data_exchange_id'].split(",") if form.cleaned_data['gtfs_data_exchange_id'] != "" else []
            agency.dev_site         = form.cleaned_data['dev_site'] if form.cleaned_data['dev_site'] != "" else None
            agency.arrival_data     = form.cleaned_data['arrival_data'] if form.cleaned_data['arrival_data'] != "" else None
            agency.position_data    = form.cleaned_data['position_data'] if form.cleaned_data['position_data'] != "" else None
            agency.standard_license = form.cleaned_data['standard_license'] if form.cleaned_data['standard_license'] != "" else None
            
            agency.location = geocode_name( agency.city, agency.state )
            agency.update_location()
            
            agency.update_slugs()
            
            agency.put()
    else:
        if agency is None:
            form = AgencyForm()
        else:
            form = AgencyForm(initial={'name':agency.name,
                                   'short_name':agency.short_name,
                                   'city':agency.city,
                                   'state':agency.state,
                                   'country':agency.country,
                                   'postal_code':agency.postal_code,
                                   'address':agency.address,
                                   'agency_url':agency.agency_url,
                                   'executive':agency.executive,
                                   'executive_email':agency.executive_email,
                                   'twitter':agency.twitter,
                                   'contact_email':agency.contact_email,
                                   'updated':agency.updated,
                                   'phone':agency.phone,
                                   'gtfs_data_exchange_id':",".join(agency.gtfs_data_exchange_id),
                                   'dev_site':agency.dev_site,
                                   'arrival_data':agency.arrival_data,
                                   'position_data':agency.position_data,
                                   'standard_license':agency.standard_license,})
    
    return render_to_response( request, "edit_agency.html", {'agency':agency, 'form':form} )
    
def agencies(request, countryslug='', stateslug='', cityslug='', nameslug=''):        

    #for a single agency:
    if nameslug:
        urlslug = '/'.join([countryslug,stateslug,cityslug,nameslug])
        agency = Agency.all().filter('urlslug =', urlslug).get()
        
        feeds = FeedReference.all().filter('gtfs_data_exchange_id IN', agency.gtfs_data_exchange_id)
        apps = TransitApp.iter_for_agency(agency)
        
        template_vars = {
            'agency': agency,
            'feeds': feeds,
            'apps': apps,
            }
    
        return render_to_response( request, "agency.html", template_vars)
    
    #return a filtered agency list
    agency_list = Agency.fetch_for_slugs(countryslug, stateslug, cityslug)

    public_filter = request.GET.get('public','all')
    public_count = no_public_count = 0
    location = ''    
    if cityslug:
        location = cityslug
    elif stateslug:
        location = stateslug 
    elif countryslug:
        location = countryslug
    
    #TODO: clean this up -- better form not to set new properties on defined model objects
    enhanced_list = [];
    for a in agency_list:
        
        if a.date_opened:
            public_count += 1
            if public_filter == 'no_public':
                a.hide = True
        else:
            no_public_count += 1
            if public_filter == 'public':
                a.hide = True
        enhanced_list.append(a)  #listify now so we dont have to do it again for count(), etc

    template_vars = {
        'agencies': agency_list,
        'location' : location,
        'public_count' : public_count,
        'public_filter' : public_filter,
        'no_public_count' : no_public_count,
        'states' : Agency.get_state_list(),
        'agency_count' : len(agency_list),
        'feed_references': FeedReference.all_by_most_recent(),
        'is_current_user_admin': users.is_current_user_admin(),
    }
    
    if request.GET.get( 'format' ) == 'json':
        jsonable_list = []
        
        for agency in agencies:
            jsonable_list.append( agency.to_jsonable() )
        
        return render_to_json(jsonable_list)
        
    if request.GET.get( 'format' ) == 'csv':
        jsonable_list = []
        
        for agency in agencies:
            jsonable_list.append( agency.to_jsonable() )
        
        if len(jsonable_list) > 0:
            csv_buffer = StringIO()
            csv_writer = csv.writer( csv_buffer )
            
            header = jsonable_list[0].keys()
            csv_writer.writerow( header )
            
            for item in jsonable_list:
                csv_writer.writerow( [item[header_col] for header_col in header] )
                        
            return HttpResponse( content=csv_buffer.getvalue(), mimetype="text/plain" )
        else:
            return HttpResponse("")
    
    return render_to_response( request, "agency_list.html", template_vars)
    
def generate_locations(request):
    """Generates Locations for all agencies in the data store. The current bulk uploader does not support adding a derived field
       during import. This is easier than writing a bulk uploader that does."""       
    pass

def admin_agencies_list(request):
    matched_gtfs_data_exchange_ids = set()
    unmatched_agencies = set()
    unmatched_feeds = set()

    # get all agencies
    for agency in Agency.all():
        # collect the gtfs_data_exchange_id of the ones that have them
        if len( agency.gtfs_data_exchange_id ) != 0:
            for gtfsdeid in agency.gtfs_data_exchange_id:
                matched_gtfs_data_exchange_ids.add( gtfsdeid )
        # the rest go into the 'unmatched agencies' bucket
        else:
            unmatched_agencies.add( agency )

    # get all feeds
    for feed in FeedReference.all():
        # the ones without ids in the matched agencies bucket go into the 'unmatched feeds' bucket
        if feed.gtfs_data_exchange_id not in matched_gtfs_data_exchange_ids:
            unmatched_feeds.add( feed )

    logging.info( unmatched_agencies )
    logging.info( unmatched_feeds )

    return render_to_response( request, "admin/agencies-list.html", {'agencies':Agency.all(),'feeds':unmatched_feeds} )

def admin_agencies_update_locations(request):
    agencies = [agency for agency in Agency.all()]
    for agency in agencies:
        agency.update_location()
    for agencies_chunk in chunk_sequence(agencies, 100):        
        db.put(agencies_chunk)
    return render_to_response(request, "admin/agencies-update-locations-finished.html")

def delete_all_agencies(request):
    keys = [key for key in Agency.all(keys_only=True)]
    for keys_chunk in chunk_sequence(keys, 100):
        db.delete(keys_chunk)
    return render_to_response(request, "admin/agencies-deleteall-finished.html")
    
def delete_agency(request,  agency_id):
    Agency.get_by_id( int( agency_id ) ).delete()
    
    return HttpResponseRedirect( "/admin/agencies/" )
    
def create_agency_from_feed(request, feed_id):
    # get feed entity
    feed = FeedReference.all().filter("gtfs_data_exchange_id =", feed_id).get()
    
    # create an agency entity from it
    agency = Agency(name = feed.name,
                    short_name = feed.name,
                    city = feed.area if feed.area!="" else "PLEASE ADD REAL CITY",
                    state = feed.state,
                    country = feed.country,
                    agency_url = feed.url,
                    gtfs_data_exchange_id = [feed_id])
    agency.put()
    
    return redirect_to( "edit_agency", agency_id = agency.key().id() )
