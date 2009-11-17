import time
import logging
from google.appengine.ext import db
from ..forms import PetitionForm, AgencyForm, AddAppForm
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..models import FeedReference, Agency
from django.template.context import RequestContext
from django.conf import settings

def wrap_tmpl_vars(request, vars=None):
    if vars is None: 
        vars = {}
    vars['GOOGLE_API_KEY'] = settings.GOOGLE_API_KEY
    vars['new_refs'] = FeedReference.all().order("-date_added")
    return RequestContext(request, vars)

def home(request):    
    new_refs = FeedReference.all().order("-date_added")
    petition_form = PetitionForm()    
    agencies = Agency.all()
    return render_to_response(request, 'home.html', wrap_tmpl_vars(request, {
        'petition_form' : petition_form, 
        'agencies' : agencies, 
        }))
    
