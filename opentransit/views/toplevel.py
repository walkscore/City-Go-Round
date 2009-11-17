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
    agencies = Agency.all()
    template_vars = {
        'petition_form': petition_form,
        'agencies': agencies,
        'feed_references': FeedReference.all_by_most_recent(),
    }    
    return render_to_response(request, 'home.html', template_vars)
    
