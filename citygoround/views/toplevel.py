import time
import logging
import csv
import StringIO

from google.appengine.ext import db
from google.appengine.api import memcache
from ..forms import PetitionForm, AgencyForm, ContactForm
from ..utils.view import render_to_response, redirect_to, not_implemented, render_to_json, render_csv
from ..utils.mailer import send_to_contact
from ..models import FeedReference, Agency, NamedStat, TransitApp
from ..decorators import memcache_view_response, requires_GET, requires_POST
from django.template.context import RequestContext
from django.conf import settings
from django.http import HttpResponseRedirect
from google.appengine.api.users import create_login_url, create_logout_url

@memcache_view_response(time = settings.MEMCACHE_PAGE_SECONDS)
def home(request):  
    template_vars = {
        'featured_apps': TransitApp.featured_by_most_recently_added().fetch(8),
        'petition_form': PetitionForm(),
        'no_getsatisfaction' : True,
        'agency_count': Agency.all().count(),
        'closed_agencies': Agency.all().filter("date_opened =", None).filter("private =", False).order("-passenger_miles"),
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
    
def admin_integrity_check(request):
    def url_for_key_and_kind(key, kind):
        if settings.RUNNING_APP_ENGINE_LOCAL_SERVER:
            return "/_ah/admin/datastore/datastore/edit?key=%s&kind=%s" % (key, kind)
        else:
            return "http://appengine.google.com/datastore/edit?app_id=citygoround&key=%s" % key
    
    # Find all model classes in our application
    from .. import models as modmod    
    model_classes = []
    for attr in dir(modmod):
        potential_class = getattr(modmod, attr)
        try:
            is_subclass = issubclass(potential_class, db.Model)
        except Exception:
            is_subclass = False
        if is_subclass:
            model_classes.append((attr, potential_class))
            
    # For each model class, identify the ReferenceProperty properties, if any...
    ref_properties = []
    ref_lists = []    
    for model_name, model_class in model_classes:
        for attr in dir(model_class):
            potential_ref = getattr(model_class, attr)
            try:
                is_key_list = False
                is_instance = isinstance(potential_ref, db.ReferenceProperty)
                
                if not is_instance:
                    is_list = isinstance(potential_ref, db.ListProperty)
                    if is_list:
                        is_key_list = (potential_ref.item_type == db.Key)
            except Exception:
                is_instance = False
                is_key_list = False
                
            if is_instance:
                ref_properties.append((model_name, model_class, attr))                
            if is_key_list:
                ref_lists.append((model_name, model_class, attr))
                
    # For each ref_property on a model, attempt to access it.
    bad_refs = []
    for model_name, model_class, property_name in ref_properties:
        for item in model_class.all():
            try:
                other_side_of_ref = eval("item." + property_name)
            except Exception:
                ref_info = {
                    "model_name": model_name,
                    "property_name": property_name,
                    "key_encoded": str(item.key()),
                    "description": str(item),
                    "inspect_url": url_for_key_and_kind(kind=model_name, key=str(item.key())),
                }
                bad_refs.append(ref_info)
    
    # For each ref_list on a model, attempt to access all keys in it.
    bad_lists = []
    for model_name, model_class, property_name in ref_lists:
        for item in model_class.all():
            keys = eval("item." + property_name)            
            for key in keys:
                try:
                    entity = db.get(key)
                except Exception:
                    list_info = {
                        "model_name": model_name,
                        "property_name": property_name,
                        "key_encoded": str(item.key()),
                        "description": str(item),
                        "inspect_url": url_for_key_and_kind(kind=model_name, key=str(item.key())),
                    }
                    bad_lists.append(list_info)
                    break
    
    # Render our status report.
    template_vars = {
        'bad_ref_count': len(bad_refs),
        'bad_refs': bad_refs,
        'bad_list_count': len(bad_lists),
        'bad_lists': bad_lists,
    }
    return render_to_response(request, 'admin/integrity-check.html', template_vars)


def comment(request):
    return render_to_response(request, 'comment.html', {})

def admin_memcache_statistics(request):
    stats = [(k, v) for k, v in memcache.get_stats().iteritems()]
    template_vars = {
        'memcache_statistics': stats,
    }
    return render_to_response(request, "admin/memcache-statistics.html", template_vars)
    
@requires_GET
def admin_memcache_statistics_json(request):
    stats = dict(memcache.get_stats())
    return render_to_json(stats)
    
@requires_POST
def admin_clear_memcache(request):
    success = memcache.flush_all()
    return render_to_json({"success": success})

@requires_GET
def admin_apps_csv(request):
    string_io = StringIO.StringIO()
    writer = csv.writer(string_io)
    writer.writerow(["APP NAME", "APP AUTHOR", "AUTHOR EMAIL", "APP HOMEPAGE", "APP DESCRIPTION", "APP IS HIDDEN"])
    for transit_app in TransitApp.query_all(visible_only = False):
        writer.writerow([transit_app.title.encode('utf8'), transit_app.author_name.encode('utf8'), str(transit_app.author_email).encode('utf8'), str(transit_app.url).encode('utf8'), transit_app.description.encode('utf8'), repr(transit_app.is_hidden).encode('utf8')])
    csv_output = string_io.getvalue()
    string_io.close()
    return render_csv(csv_output)

