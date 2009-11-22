# NOTE: Must import *, since Django looks for things here, e.g. handler500.
from django.conf.urls.defaults import *

urlpatterns = patterns('')

# Top Level Views -- Home Page, about, etc.
urlpatterns += patterns(
    'opentransit.views.toplevel',
    url(r'^$', 'home', name='home'),
    url(r'^contact/$', 'contact', name='contact'),
    url(r'^contact-thanks/$', 'contact_thanks', name='contact_thanks'),
    url(r'^about/$', 'static', {'template':'about.html'}, name='about'),
    url(r'^opensource/$', 'static', {'template':'opensource.html'}, name='opensource'),
    url(r'^petition-signed/$', 'static', {'template':'petition_signed.html'}, name='petition_signed'),
    url(r'^admin/login/$', 'admin_login'),
    url(r'^admin/logout/$', 'admin_logout'),
    url(r'^admin/$', 'debug', name='debug'),
)


# Petition Views -- Currently only has examples
urlpatterns += patterns(
    'opentransit.views.petition',
    url(r'^example_petition_form/$', 'example_petition_form', name='example_petition_form'),
    url(r'^example_petition_success/$', 'example_petition_success', name='example_petition_success'),
)


# Feed Views -- Lists, Update Hooks, etc.
urlpatterns += patterns(
    'opentransit.views.feed',
    url(r'^admin/feeds/update/$', 'update_feed_references', name='update_feed_references'),
    url(r'^feed-references/$', 'feed_references', name='feed_references'),
)


# Agency Views -- Full URL structure for viewing agencies, and for adding/editing them
urlpatterns += patterns(
    'opentransit.views.agency',
    url(r'^admin/agencies/edit/(?P<agency_id>\d+)/$', 'edit_agency', name='edit_agency'), #todo: move this to /agencies/..../edit url
    url(r'^agencies/$', 'agencies', name='agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/(?P<stateslug>[\w-]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/(?P<stateslug>[\w-]+)/(?P<cityslug>[\w-]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/(?P<stateslug>[\w-]+)/(?P<cityslug>[\w-]+)/(?P<nameslug>[\w-]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/(?P<stateslug>[\w-]+)/(?P<cityslug>[\w-]+)/(?P<nameslug>[\w-]+)/edit/$', 'edit_agency'),
    url(r'^agencies/(?P<agency>\d+)/$', 'agencies'),
    url(r'^admin/agencies/deleteall/$', 'delete_all_agencies'),
    url(r'^admin/agencies/delete/(?P<agency_id>\d+)/$', 'delete_agency', name='delete_agency'),
    url(r'^admin/agencies/create-from-feed/(?P<feed_id>[-\w ]+)/$', 'create_agency_from_feed', name='admin_agencies_create_from_feed'),
    url(r'^admin/agencies/add/$', 'edit_agency', name='edit_agency'),
    url(r'^admin/agencies/update-locations/$', 'admin_agencies_update_locations', name='admin_agencies_update_locations'),    
)


# Apps Views -- Full URL structure for viewing transit apps, and for adding/editing them
urlpatterns += patterns(
    'opentransit.views.app',
    url(r'^apps/$', 'gallery', name='apps_gallery'),
    url(r'^apps/nearby/$', 'nearby', name='apps_nearby'),
    url(r'^apps/add/$', 'add_form', name='apps_add_form'),
    url(r'^apps/add/locations/(?P<progress_uuid>[\w]+)/$', 'add_locations', name='apps_add_locations'),
    url(r'^apps/add/agencies/(?P<progress_uuid>[\w]+)/$', 'add_agencies', name='apps_add_agencies'),
    url(r'^apps/add/success/$', 'add_success', name='apps_add_success'),
    url(r'^apps/(?P<transit_app_slug>[\w-]+)/$', 'details', name='apps_details'),
    url(r'^apps/(?P<transit_app_slug>[\w-]+)/screenshot.png$', 'screenshot', name='apps_screenshot'),
)


# API Views -- All URLs that return JSON (maybe XML in the future) back. 
# Want to break these out just to make clear what our programmatic API surface is.
urlpatterns += patterns(
    'opentransit.views.api',
    url(r'^api/agencies/search/$', 'api_agencies_search', name = 'api_agencies_search'),    
    url(r'^api/apps/search/$', 'api_apps_search', name = 'api_apps_search'),
    url(r'^api/agencies/for-app/(?P<transit_app_slug>[\w-]+)/$', 'api_agencies_for_app', name = 'api_agencies_for_app'),
    url(r'^api/apps/for-agency/(?P<key_encoded>[\w-]+)/$', 'api_apps_for_agency', name = 'api_apps_for_agency'),
    url(r'^api/agencies/for-apps/$', 'api_agencies_for_apps', name = 'api_agencies_for_apps'),
    url(r'^api/apps/for-agencies/$', 'api_apps_for_agencies', name = 'api_apps_for_agencies'),
)
    
    
