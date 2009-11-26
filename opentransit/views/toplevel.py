import time
import logging
from google.appengine.ext import db
from ..forms import PetitionForm, AgencyForm, ContactForm
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..utils.mailer import send_to_contact
from ..models import FeedReference, Agency, NamedStat, TransitApp
from django.template.context import RequestContext
from django.conf import settings
from django.http import HttpResponseRedirect
from google.appengine.api.users import create_login_url, create_logout_url

def home(request):  

    template_vars = {
        'featured_apps': TransitApp.all(),
        'petition_form': PetitionForm(),
        'no_getsatisfaction' : True,
        'agency_count': Agency.all().count(),
        'closed_agencies': Agency.all().filter("date_opened =", None).order("-passenger_miles"),
        'open_agencies': Agency.all().filter("date_opened !=", None).order("-date_opened"),
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

def admin_home(request):
    all_stats = NamedStat.all()
    
    return render_to_response(request, 'admin/home.html', {'all_stats':all_stats})
    
