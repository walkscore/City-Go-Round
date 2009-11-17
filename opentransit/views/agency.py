import time
import logging
from google.appengine.ext import db

from ..forms import AgencyForm
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..models import Agency

from django.http import HttpResponse
from ..utils.slug import slugify

def edit_agency(request, agency_id):
    agency = Agency.get_by_id( int(agency_id) )
    
    if request.method == 'POST':
        form = AgencyForm(request.POST)
        if form.is_valid():
            agency.name       = form.cleaned_data['name']
            agency.short_name = form.cleaned_data['short_name']
            agency.tier       = form.cleaned_data['tier']
            agency.city       = form.cleaned_data['city']
            agency.state      = form.cleaned_data['state']
            agency.country    = form.cleaned_data['country']
            agency.postal_code      = form.cleaned_data['postal_code']
            agency.address          = form.cleaned_data['address']
            agency.agency_url       = form.cleaned_data['agency_url']
            agency.executive        = form.cleaned_data['executive']
            agency.executive_email  = form.cleaned_data['executive_email'] if form.cleaned_data['executive_email'] != "" else None
            agency.twitter          = form.cleaned_data['twitter']
            agency.contact_email    = form.cleaned_data['contact_email']
            agency.updated          = form.cleaned_data['updated']
            agency.phone            = form.cleaned_data['phone']
            agency.put()
    else:
        form = AgencyForm(initial={'name':agency.name,
                               'short_name':agency.short_name,
                               'tier':agency.tier,
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
                               'phone':agency.phone})
    
    return render_to_response( request, "edit_agency.html", {'agency':agency, 'form':form} )
    
def all_agencies(request):
    agencies = Agency.all().order("name")

    return render_to_response( request, "agency_list.html", {'agencies':agencies, } )

def generate_slugs(request):
    """Generates slugs for all agencies in the data store. The current bulk uploader does not support adding a derived field
       during import. This is easier than writing a bulk uploader that does."""
       
    for agency in Agency.all():
        agency.urlslug = slugify(agency.state)+"/"+slugify(agency.city)+"/"+slugify(agency.name)
        agency.put()
    
    return HttpResponse( "slugs generated" )

def agency(request, urlslug):
    agency = Agency.all().filter('urlslug =', urlslug).get()
    
    return render_to_response( request, "agency.html", {'agency':agency} )