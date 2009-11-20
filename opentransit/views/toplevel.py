import time
import logging
from google.appengine.ext import db
from ..forms import PetitionForm, AgencyForm, ContactForm
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..utils.mailer import send_to_contact
from ..models import FeedReference, Agency
from django.template.context import RequestContext
from django.conf import settings

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
    
def faq(request):  
    return render_to_response(request, 'faq.html')

def about(request):  
    return render_to_response(request, 'about.html')
    
def petition_signed(request):  
    return render_to_response(request, 'petition_signed.html')
