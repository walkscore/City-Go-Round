# NOTE: Must import *, since Django looks for things here, e.g. handler500.
from django.conf.urls.defaults import *

urlpatterns = patterns('')

# Top Level Views -- Home Page, about, etc.
urlpatterns += patterns(
    'opentransit.views.toplevel',
    url(r'^$', 'home', name='home'),
    url(r'^contact/$', 'contact', name='contact'),
    url(r'^contact-thanks/$', 'contact_thanks', name='contact_thanks'),
    url(r'^faq/$', 'faq', name='faq'),
    url(r'^about/$', 'about', name='about'),
    url(r'^petition-signed/$', 'petition_signed', name='petition_signed'),
)


# Petition Views -- Currently only has examples
urlpatterns += patterns(
    'opentransit.views.petition',
    url(r'^example_petition_form$', 'example_petition_form', name='example_petition_form'),
    url(r'^example_petition_success$', 'example_petition_success', name='example_petition_success'),
)


# Feed Views -- Lists, Update Hooks, etc.
urlpatterns += patterns(
    'opentransit.views.feed',
    url(r'^admin/feeds/update$', 'update_feed_references', name='update_feed_references'),
    url(r'^feed-references$', 'feed_references', name='feed_references'),
)


# Agency Views -- Full URL structure for viewing agencies, and for adding/editing them
urlpatterns += patterns(
    'opentransit.views.agency',
    url('^agencies/edit/(?P<agency_id>\d+)/$', 'edit_agency', name='edit_agency'), #todo: move this to /agencies/..../edit url
    url(r'^agencies/$', 'agencies'),
    url(r'^agencies/search/$', 'agencies_search'),
    url(r'^agencies/(?P<countryslug>[-\w ]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[-\w ]+)/(?P<stateslug>[-\w ]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[-\w ]+)/(?P<stateslug>[-\w ]+)/(?P<cityslug>[-\w ]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[-\w ]+)/(?P<stateslug>[-\w ]+)/(?P<cityslug>[-\w ]+)/(?P<nameslug>[-\w]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[-\w ]+)/(?P<stateslug>[-\w ]+)/(?P<cityslug>[-\w ]+)/(?P<nameslug>[-\w]+)/edit/$', 'edit_agency'),
    url(r'^agencies/(?P<agency>\d+)/$', 'agencies'),
    url(r'^admin/agencies/delete/$', 'delete_all_agencies')
)


# Apps Views -- Full URL structure for viewing transit apps, and for adding/editing them
urlpatterns += patterns(
    'opentransit.views.app',
    url(r'^apps/$', 'gallery', name='apps_gallery'),
    url(r'^apps/nearby/$', 'nearby', name='apps_nearby'),
    url(r'^apps/add/$', 'add_form', name='apps_add_form'),
    url(r'^apps/add/locations/$', 'add_locations', name='apps_add_locations'),
    url(r'^apps/add/success/$', 'add_success', name='apps_add_success'),
    url(r'^apps/(?P<transit_app_slug>[\w-]+)/$', 'details', name='apps_details'),
    url(r'^apps/(?P<transit_app_slug>[\w-]+)/screenshot.png$', 'screenshot', name='apps_screenshot'),
)