import time
import logging
from google.appengine.ext import db
from ..forms import PetitionForm, AgencyForm, ContactForm
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..utils.mailer import send_to_contact
from ..models import FeedReference, Agency
from django.template.context import RequestContext
from django.conf import settings
from django.http import HttpResponseRedirect
from google.appengine.api.users import create_login_url, create_logout_url

def home(request):    
    petition_form = PetitionForm()
    
    agency_count = Agency.all().count()
    
    closed_agencies = Agency.all().filter("date_opened =", None).order("-passenger_miles")
    open_agencies = Agency.all().filter("date_opened !=", None).order("-date_opened")
    
    logging.info( closed_agencies.count() )
    logging.info( open_agencies.count() )
    
    template_vars = {
        'petition_form': petition_form,
        'agency_count': agency_count,
        'closed_agencies': closed_agencies,
        'open_agencies': open_agencies,
    }    
    return render_to_response(request, 'home.html', template_vars)

def contact(request):    
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():                    
          
            send_to_contact("[CityGoRound contact form] " + contact_form.cleaned_data['name'] + ", " + contact_form.cleaned_data['email'], contact_form.cleaned_data['message']);
          
            # Done!
            return redirect_to('contact_thanks')

    else:
        contact_form = ContactForm()

    template_vars = {
        'contact_form': contact_form
    }    
    return render_to_response(request, 'contact.html', template_vars)

def contact_thanks(request):    
    petition_form = PetitionForm()    
    template_vars = {
        'petition_form': petition_form
    }    

    return render_to_response(request, 'contact-thanks.html', template_vars)

def static(request, template):
    return render_to_response(request, template)
    
def admin_login(request):
    return HttpResponseRedirect( create_login_url("/") )
    
def admin_logout(request):
    return HttpResponseRedirect( create_logout_url("/") )
    
def debug(request):
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
    
    return render_to_response( request, "feed-merge.html", {'agencies':Agency.all(),'feeds':unmatched_feeds} )
    
