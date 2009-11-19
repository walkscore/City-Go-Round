import time
import logging
from google.appengine.ext import db
from ..forms import PetitionForm, AgencyForm, AddAppForm
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..models import FeedReference, Agency
from django.template.context import RequestContext
from django.conf import settings

def home(request):    
    petition_form = PetitionForm()
    
    agency_count = Agency.all().count()
    
    closed_agencies = Agency.all().filter("date_opened =", None).order("-service_area_population")
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
    
