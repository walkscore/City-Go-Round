import time
import logging
 
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
 
from ..decorators import memcache_parameterized_view_response
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

def agency_app_counts(request):
    return render_to_json( TransitApp.agency_app_counts() )

def safe_str(item):
    """it's like applying str() but it won't cause ascii encoding problems down the line"""

    if type(item)==str or type(item)==unicode:
        return item.encode("utf8")
    else:
        return str(item)

@memcache_parameterized_view_response(time = settings.MEMCACHE_PAGE_SECONDS)  
def agencies(request, countryslug='', stateslug='', cityslug='', nameslug=''):        
    # TODO davepeck: I just looked at this code -- we _really_ need to clean this stuff up
    # and rationalize it with our API. I think this code is doing 'far too much dude'

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

    if request.GET.get( 'format' ) == 'json':
        jsonable_list = []
        
        for agency in agency_list:
            jsonable_list.append( agency.to_jsonable() )
        
        return render_to_json(jsonable_list)
        
    if request.GET.get( 'format' ) == 'csv':
        jsonable_list = []
        
        for agency in agency_list:
            jsonable_list.append( agency.to_jsonable() )
        
        if len(jsonable_list) > 0:
            csv_buffer = StringIO()
            csv_writer = csv.writer( csv_buffer )
            
            header = jsonable_list[0].keys()
            csv_writer.writerow( header )
            
            for item in jsonable_list:
                csv_writer.writerow( [safe_str(item[header_col]) for header_col in header] )
                        
            return HttpResponse( content=csv_buffer.getvalue(), mimetype="text/csv" )
        else:
            return HttpResponse( content="", mimetype="text/csv")

    public_filter = request.GET.get('public','all')
    public_count = no_public_count = 0
    location = {'country':None,'state':None,'city':None}
    if cityslug:
        location['city'] = cityslug
    if stateslug:
        location['state'] = stateslug
    if countryslug:
        location['country'] = countryslug
    location_string = cityslug or stateslug or countryslug
    
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


    if countryslug:
        page_title = "%s transit agencies on City-Go-Round" % location_string.upper();
    else:
        page_title = "List of Public Transit Agencies on City-Go-Round"    
    
    template_vars = {
        'agencies': agency_list,
        'location' : location,
        'location_string' : location_string,
        'public_count' : public_count,
        'public_filter' : public_filter,
        'no_public_count' : no_public_count,
        'states' : Agency.get_state_list(),
        'countries' : Agency.get_country_list(),
        'agency_count' : len(agency_list),
        'feed_references': FeedReference.all_by_most_recent(),
        'is_current_user_admin': users.is_current_user_admin(),
        'page_title': page_title,
        'page_url':request.META['PATH_INFO']+"?"+request.META['QUERY_STRING'],
    }
    
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
    agency = Agency.get_by_id(int(agency_id))

    # If any applications _explicitly_ support this agency, go ahead and remove that explicit support...
    explicit_apps = TransitApp.fetch_for_explicit_agency(agency)
    for explicit_app in explicit_apps:
        explicit_app.remove_explicitly_supported_agency(agency)
    
    # Save the apps.
    for explicit_app_chunk in chunk_sequence(explicit_apps, 10):
        db.put(explicit_app_chunk)

    # Now, delete the agency.
    agency.delete()
    
    return redirect_to("admin_agencies_list")
    
def create_agency_from_feed(request, feed_id):
    # get feed entity
    feed = FeedReference.all().filter("gtfs_data_exchange_id =", feed_id).get()
    
    # create an agency entity from it
    agency = Agency(name = feed.name,
                    short_name = feed.name,
                    city = feed.area if feed.area!="" else "PLEASE ADD REAL CITY",
                    state = feed.state if feed.state!="" else "PLEASE ADD REAL STATE",
                    country = feed.country,
                    agency_url = feed.url,
                    gtfs_data_exchange_id = [feed_id])
    agency.put()
    
    return redirect_to( "edit_agency", agency_id = agency.key().id() )
    
def make_everything_public(request):
    """Added the 'private' property to Agencies after launch; this initializes them"""
    
    # This method is really big and nasty because at one point the index got corrupted and I had to figure out a way
    # to hit and re-put every single element without timing out.
    #
    # This method isn't really useful anymore. If there are no bugs in the Agency.private system beyoond a couple
    # weeks after Jan 10 2010, you should delete this and spare yourself the eyesore
    
    things_an_agency_can_be = {}
    
    n=int(request.GET.get("n",1000))
    offset=int(request.GET.get("offset",0))
    
    i=0
    count=0
    for agency in Agency.all().fetch(n, offset):
        things_an_agency_can_be[agency.private] = things_an_agency_can_be.get(agency.private,0)+1
        
        if agency.private != True:
            agency.private = False
            agency.put()
            i+=1
        count += 1
    
    all_public_count = Agency.all().filter("private =", False).count()
    all_private_count = Agency.all().filter("private =", True).count()
    all_all_count = Agency.all().count()
        
    return HttpResponse("n:%d offset:%d, flipped the public bit on %d agencies (%d public %d private %d nothing %d all %d count %s histogram)"%(n, offset, i, all_public_count, all_private_count, i, all_all_count, count, things_an_agency_can_be) )
