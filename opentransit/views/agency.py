import time
import logging
from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.api import memcache
from geo import geotypes

from ..forms import AgencyForm
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..models import Agency, FeedReference, TransitApp

from django.http import HttpResponse
from ..utils.slug import slugify


def uniquify(seq): 
    # not order preserving 
    set = {} 
    map(set.__setitem__, seq, []) 
    return set.keys()


def edit_agency(request, agency_id):
    agency = Agency.get_by_id( int(agency_id) )
    
    if request.method == 'POST':
        form = AgencyForm(request.POST)
        if form.is_valid():
            agency.name       = form.cleaned_data['name']
            agency.short_name = form.cleaned_data['short_name']
            agency.city       = form.cleaned_data['city']
            agency.state      = form.cleaned_data['state']
            agency.country    = form.cleaned_data['country']
            agency.postal_code      = form.cleaned_data['postal_code']
            agency.address          = form.cleaned_data['address']
            agency.agency_url       = form.cleaned_data['agency_url']
            agency.executive        = form.cleaned_data['executive']
            agency.executive_email  = form.cleaned_data['executive_email'] if form.cleaned_data['executive_email'] != "" else None
            agency.twitter          = form.cleaned_data['twitter']
            agency.contact_email    = form.cleaned_data['contact_email'] if form.cleaned_data['contact_email'] != "" else None
            agency.updated          = form.cleaned_data['updated']
            agency.phone            = form.cleaned_data['phone']
            agency.gtfs_data_exchange_id      = form.cleaned_data['gtfs_data_exchange_id']
            agency.put()
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
                               'gtfs_data_exchange_id':agency.gtfs_data_exchange_id})
    
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
        
        feeds = FeedReference.all().filter('gtfs_data_exchange_id =', agency.gtfs_data_exchange_id)
        
        template_vars = {
            'agency': agency,
            'feeds': feeds,
            }
    
        return render_to_response( request, "agency.html", template_vars)
    location = 'system'
    
    agencies = Agency.all().order("name")
    mck = 'agencies'
    if countryslug:
        agencies = agencies.filter('countryslug =',countryslug)
        mck = 'agencies_%s' % countryslug
        location = countryslug
    if stateslug:
        agencies = agencies.filter('stateslug =', stateslug)
        logging.debug('filtering by stateslug %s' % stateslug)
        mck = 'agencies_%s_%s' % (countryslug, stateslug)
        location = stateslug 
    if cityslug:
        agencies = agencies.filter('cityslug =', cityslug)
        logging.debug('filtering by cityslug %s' % cityslug)
        mck = 'agencies_%s_%s_%s' % (countryslug, stateslug, cityslug)
        location = cityslug
    
    mem_result = memcache.get(mck)
    if not mem_result:
        agencies = agencies.order("name")
        mc_added = memcache.add(mck, agencies, 60 * 1)
    else:
        agencies = mem_result
    
    agency_list = []
    public_count = no_public_count = 0
    
    for a in agencies:
        if a.date_opened:
            public_count += 1
        else:
            no_public_count += 1
        agency_list.append(a)  #listify now so we dont have to do it again for count(), etc

    template_vars = {
        'agencies': agency_list,
        'location' : location,
        'public_count' : public_count,
        'no_public_count' : no_public_count,
        'states' : get_state_list(),
        'agency_count' : len(agency_list),
        'feed_references': FeedReference.all_by_most_recent(),
    }
    
    if request.GET.get( 'format' ) == 'json':
        jsonable_list = []
        
        for agency in agencies:
            jsonable_list.append( agency.to_jsonable() )
        
        return HttpResponse( content=json.dumps( jsonable_list, indent=2 ), mimetype="text/plain" )
    
    return render_to_response( request, "agency_list.html", template_vars)
    
def generate_locations(request):
    """Generates Locations for all agencies in the data store. The current bulk uploader does not support adding a derived field
       during import. This is easier than writing a bulk uploader that does."""
       
    pass
    return HttpResponse( "locations NOT generated" )

def agencies_search(request):
    """
    params
     - type (location or city)
     - lat/lon [location]
     - city/state [city]
    returns:
     list of nearby (location) or matching (city) agencies, and their associated apps
    """
    def agencies_to_json(agencies):
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
    format = rg('format','')
    
    agencies = Agency.all()
    if not search_type in ['location', 'city']:
        return HttpResponse('404 - invalid search type')
    if search_type == 'location':
        #get all agencies that are nearby
        lat,lon = check_lat_lon(lat, lon)
        if not (lat and lon):
            return HttpResponse('404 - invalid lat/lng')
        r = .25
        agencies = Agency.bounding_box_fetch(
            agencies,
            geotypes.Box(lat+r, lon+r, lat-r, lon-r),
            max_results = 50)
        
    if search_type == 'city':
        logging.debug('filtering by city %s' % city)
        if not (city and state):
            return HttpResponse('404 - you must include city and state params')
        #get all agencies matching a state and city
        agencies = agencies.filter('state =',state.upper()).filter('city =',city)
    
    if format == 'json':
        return HttpResponse(json.dumps(agencies_to_json(agencies)), mimetype='text/html')
    else:
        return render_to_response( request, "agency_search.html", {'agencies' : agencies} )
        
def delete_all_agencies(request):
    for agency in Agency.all():
        agency.delete()
        
    return HttpResponse( "deleted all agencies")
    
