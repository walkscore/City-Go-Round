import time
import logging
from google.appengine.ext import db
from google.appengine.api import memcache
from geo import geotypes

from ..forms import AgencyForm
from ..utils.view import render_to_response, redirect_to, not_implemented, bad_request, render_to_json
from ..models import Agency, FeedReference, TransitApp

from django.http import HttpResponse, HttpResponseRedirect
from ..utils.slug import slugify

from StringIO import StringIO
import csv
from google.appengine.api import users


def uniquify(seq): 
    # not order preserving 
    set = {} 
    map(set.__setitem__, seq, []) 
    return set.keys()

def edit_agency(request, agency_id=None):
    if agency_id is not None:
        agency = Agency(name=form.cleaned_data['name'])
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

    def get_state_list():
        #factoring this out since we want all states all the time
        #and because we want to memcache this
        #todo: add other countries (return dict where value includes proper url)
        mem_result = memcache.get('all_states')
        if not mem_result:
            states = uniquify([a.stateslug for a in Agency.all()])
            states.sort()
            mc_added = memcache.add('all_states', states, 60 * 1)
        else:
            states = mem_result

        return states
        

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
    location = ''
    
        
    mck = 'agencies'
    if cityslug:
        logging.debug('filtering by cityslug %s' % cityslug)
        mck = 'agencies_%s_%s_%s' % (countryslug, stateslug, cityslug)
        location = cityslug
    elif stateslug:
        logging.debug('filtering by stateslug %s' % stateslug)
        mck = 'agencies_%s_%s' % (countryslug, stateslug)
        location = stateslug 
    elif countryslug:
        mck = 'agencies_%s' % countryslug
        location = countryslug
    
    mem_result = memcache.get(mck)
    if mem_result:
        agencies = mem_result    
    else:
        agencies = Agency.all().order("name")    
        if cityslug:
            agencies = agencies.filter('cityslug =', cityslug)
        elif stateslug:
            agencies = agencies.filter('stateslug =', stateslug)
        elif countryslug:
            agencies = agencies.filter('countryslug =',countryslug)

        mc_added = memcache.add(mck, agencies, 60 * 1)
    
    agency_list = []
    public_count = no_public_count = 0
    public_filter = request.GET.get('public','')
    
    for a in agencies:
        if a.date_opened:
            public_count += 1
            a.date_opened_formatted = a.date_opened
            if public_filter == 'no_public':
                a.hide = True
        else:
            no_public_count += 1
            if public_filter == 'public':
                a.hide = True
        agency_list.append(a)  #listify now so we dont have to do it again for count(), etc

    template_vars = {
        'agencies': agency_list,
        'location' : location,
        'public_count' : public_count,
        'public_filter' : public_filter,
        'no_public_count' : no_public_count,
        'states' : get_state_list(),
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

def agencies_search(request):
    """
    params
     - type (location or city)
     - lat/lon [location]
     - city/state [city]
    returns:
     list of nearby (location) or matching (city) agencies, and their associated apps
    """
    def agencies_to_dictionary(agencies):
        ag = {'agencies' : []}
        for a in agencies:
            ad = {}
            for k in 'name,city,urlslug,state'.split(','):
                ad[k] = getattr(a,k)
            #unsure how to get apps...
            ad['apps'] = list(TransitApp.iter_for_agency(a))
            ag['agencies'].append(ad)
        ag['apps'] = list(TransitApp.iter_for_agencies(agencies))
        return ag                

    def check_lat_lon(lat, lon):
        try:
            return float(lat), float(lon)
        except:
            return (0,0)
        
    #ensure location type search
    rg = request.GET.get
    search_type = rg('type','')
    lat = rg('lat','')
    lon = rg('lon','')
    city = rg('city','')
    state = rg('state','')
    format = rg('format','html')

    if not search_type in ['location', 'city', 'state']:
        return bad_request('invalid search type')
        
    if not format in ['html', 'json']:
        return bad_request('invalid format')
    
    agencies = Agency.all()
    
    if search_type == 'location':
        #get all agencies that are nearby
        lat,lon = check_lat_lon(lat, lon)
        if not (lat and lon):
            return bad_request('invalid lat/lng')
        r = .25
        agencies = Agency.bounding_box_fetch(
            agencies,
            geotypes.Box(lat+r, lon+r, lat-r, lon-r),
            max_results = 50)        
    else:
        if search_type == 'city':
            if not city:
                return bad_request('you must include a city')
            # NOTE davepeck: we used to search for 'city =', city... but that didn't really
            # work because of differences in capitalization. Use slugs instead.
            agencies = agencies.filter('cityslug =', slugify(city))
        if not state:
            return bad_request('you must include a state')
        agencies = agencies.filter('state =', state.upper())        
    
    if format == 'json':
        return render_to_json(agencies_to_dictionary(agencies))
    else:
        return not_implemented(request) # We haven't written "agency_search.html" yet.
        
def delete_all_agencies(request):
    todelete = list(Agency.all(keys_only=True))
    
    for i in range(0, len(todelete), 500):
        db.delete( todelete[i:i+500] )
        
    return HttpResponse( "deleted all agencies")
    
def create_agency_from_feed(request, feed_id):
    # get feed entity
    feed = FeedReference.all().filter("gtfs_data_exchange_id =", feed_id).get()
    
    # create an agency entity from it
    agency = Agency(name = feed.name,
                    short_name = feed.name,
                    city = feed.area if feed.area!="" else "cowtown",
                    state = feed.state,
                    country = feed.country,
                    agency_url = feed.url,
                    gtfs_data_exchange_id = [feed_id])
    agency.put()
    
    return HttpResponseRedirect( "/agencies/edit/%s/"%agency.key().id() )
