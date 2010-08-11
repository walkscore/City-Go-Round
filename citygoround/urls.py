# NOTE: Must import *, since Django looks for things here, e.g. handler500.
from django.conf.urls.defaults import *

urlpatterns = patterns('')

# Top Level Views -- Home Page, about, etc.
urlpatterns += patterns(
    'citygoround.views.toplevel',
    url(r'^$', 'home', name='home'),
    url(r'^comment/$', 'comment', name='comment'),
    url(r'^contact/$', 'contact', name='contact'),
    url(r'^contact-thanks/$', 'contact_thanks', name='contact_thanks'),
    url(r'^about/$', 'static', {'template':'about.html'}, name='about'),
    url(r'^opensource/$', 'static', {'template':'opensource.html'}, name='opensource'),
    url(r'^petition-signed/$', 'static', {'template':'petition_signed.html'}, name='petition_signed'),
    url(r'^widgets/$', 'static', {'template':'widgets.html'}, name='widgets'),
    url(r'^terms-of-use/$', 'static', {'template':'terms_of_use.html'}, name='terms_of_use'),
    url(r'^admin/login/$', 'admin_login'),
    url(r'^admin/logout/$', 'admin_logout'),
    url(r'^admin/$', 'admin_home', name='admin_home'),
    url(r'^admin/integrity-check/$', 'admin_integrity_check', name='admin_integrity_check'),
    url(r'^admin/memcache-statistics/$', 'admin_memcache_statistics', name='admin_memcache_statistics'),
    url(r'^admin/memcache-statistics/json/$', 'admin_memcache_statistics_json', name='admin_memcache_statistics_json'),
    url(r'^admin/clear-memcache/$', 'admin_clear_memcache', name='admin_clear_memcache'),
    url(r'^admin/all-transit-apps.csv$', 'admin_apps_csv', name='admin_apps_csv'),
)


# Petition Views -- Currently only has examples
urlpatterns += patterns(
    'citygoround.views.petition',
    url(r'^example_petition_form/$', 'example_petition_form', name='example_petition_form'),
    url(r'^example_petition_success/$', 'example_petition_success', name='example_petition_success'),
)


# Feed Views -- Lists, Update Hooks, etc.
urlpatterns += patterns(
    'citygoround.views.feed',
    url(r'^admin/feeds/update/$', 'update_feed_references', name='update_feed_references'),
    url(r'^admin/feeds/delete/$', 'delete_all_feed_references', name='delete_all_feed_references'),
    url(r'^admin/feeds/references/$', 'admin_feed_references', name='admin_feed_references'),
)


# Agency Views -- Full URL structure for viewing agencies, and for adding/editing them
urlpatterns += patterns(
    'citygoround.views.agency',
    url(r'^agencies/$', 'agencies', name='agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/(?P<stateslug>[\w-]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/(?P<stateslug>[\w-]+)/(?P<cityslug>[\w-]+)/$', 'agencies'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/(?P<stateslug>[\w-]+)/(?P<cityslug>[\w-]+)/(?P<nameslug>[\w-]+)/$', 'agencies', name='agencies_all_slugs'),
    url(r'^agencies/(?P<countryslug>[\w-]+)/(?P<stateslug>[\w-]+)/(?P<cityslug>[\w-]+)/(?P<nameslug>[\w-]+)/edit/$', 'edit_agency'),
    url(r'^agencies/(?P<agency>\d+)/$', 'agencies'),
    url(r'^admin/agencies/$', 'admin_agencies_list', name='admin_agencies_list'),    
    url(r'^admin/agencies/edit/(?P<agency_id>\d+)/$', 'edit_agency', name='edit_agency'),
    url(r'^admin/agencies/deleteall/$', 'delete_all_agencies'),
    url(r'^admin/agencies/delete/(?P<agency_id>\d+)/$', 'delete_agency', name='delete_agency'),
    url(r'^admin/agencies/create-from-feed/(?P<feed_id>[-\w ]+)/$', 'create_agency_from_feed', name='admin_agencies_create_from_feed'),
    url(r'^admin/agencies/add/$', 'edit_agency', name='admin_agencies_add'),
    url(r'^admin/agencies/update-locations/$', 'admin_agencies_update_locations', name='admin_agencies_update_locations'),
    url(r'^admin/agencies/appcounts/$', 'agency_app_counts', name='agency_app_counts'),
    url(r'^admin/agencies/makepublic/$', 'make_everything_public', name='make_everything_public'),
)


# Apps Views -- Full URL structure for viewing transit apps, and for adding/editing them
urlpatterns += patterns(
    'citygoround.views.app',
    url(r'^apps/$', 'gallery', name='apps_gallery'),
    url(r'^apps/nearby/$', 'nearby', name='apps_nearby'),
    url(r'^apps/add/$', 'add_form', name='apps_add_form'),
    url(r'^apps/add/locations/(?P<progress_uuid>[\w]+)/$', 'add_locations', name='apps_add_locations'),
    url(r'^apps/add/agencies/(?P<progress_uuid>[\w]+)/$', 'add_agencies', name='apps_add_agencies'),
    url(r'^apps/add/success/$', 'add_success', name='apps_add_success'),
    url(r'^apps/(?P<transit_app_slug>[\w-]+)/$', 'details', name='apps_details'),
    url(r'^apps/(?P<transit_app_slug>[\w-]+)/location/$', 'app_location', name='app_location'),
    url(r'^apps/(?P<transit_app_slug>[\w-]+)/screenshot-(?P<screen_shot_index>[\d]+)-(?P<screen_shot_size_name>[\w\d]+).png$', 'screenshot', name='apps_screenshot'),
    url(r'^apps/(?P<transit_app_slug>[\w-]+)/rating/vote/$', 'app_rating_vote', name='app_rating_vote'),    
    url(r'^admin/apps/$', 'admin_apps_list', name='admin_apps_list'),
    url(r'^admin/apps/edit/(?P<transit_app_slug>[\w-]+)/$', 'admin_apps_edit', name='admin_apps_edit'),
    url(r'^admin/apps/edit/(?P<transit_app_slug>[\w-]+)/basic/$', 'admin_apps_edit_basic', name='admin_apps_edit_basic'),
    url(r'^admin/apps/edit/(?P<transit_app_slug>[\w-]+)/locations/$', 'admin_apps_edit_locations', name='admin_apps_edit_locations'),
    url(r'^admin/apps/edit/(?P<transit_app_slug>[\w-]+)/agencies/$', 'admin_apps_edit_agencies', name='admin_apps_edit_agencies'),
    url(r'^admin/apps/edit/(?P<transit_app_slug>[\w-]+)/images/$', 'admin_apps_edit_images', name='admin_apps_edit_images'),
    url(r'^admin/apps/delete/(?P<transit_app_slug>[\w-]+)/$', 'admin_apps_delete', name='admin_apps_delete'),
    url(r'^admin/apps/hide-unhide/(?P<transit_app_slug>[\w-]+)/$', 'admin_apps_hide_unhide', name='admin_apps_hide_unhide'),
    url(r'^admin/apps/bayes/refresh/$', 'refresh_all_bayesian_averages', name='refresh_all_bayesian_averages'),
    url(r'^admin/apps/update-schema/$', 'admin_apps_update_schema', name='admin_apps_update_schema'),
)


# API Views -- All URLs that return JSON (maybe XML in the future) back. 
# Want to break these out just to make clear what our programmatic API surface is.
urlpatterns += patterns(
    'citygoround.views.api',
    url(r'^api/agencies/search/$', 'api_agencies_search', name = 'api_agencies_search'),    
    url(r'^api/agencies/all/$', 'api_agencies_all', name = 'api_agencies_all'),
    url(r'^api/apps/search/$', 'api_apps_search', name = 'api_apps_search'),
    url(r'^api/apps/all/$', 'api_apps_all', name = 'api_apps_all'),
    url(r'^api/agencies/for-app/(?P<transit_app_slug>[\w-]+)/$', 'api_agencies_for_app', name = 'api_agencies_for_app'),
    url(r'^api/apps/for-agency/(?P<key_encoded>[\w-]+)/$', 'api_apps_for_agency', name = 'api_apps_for_agency'),
    url(r'^api/agencies/for-apps/$', 'api_agencies_for_apps', name = 'api_agencies_for_apps'),
    url(r'^api/apps/for-agencies/$', 'api_apps_for_agencies', name = 'api_apps_for_agencies'),
)
    
# Task Queue Views -- All URLs that service task queue items
urlpatterns += patterns(
    'citygoround.views.taskqueue',
    url(r'^admin/taskqueue/screen-shot-resize/', 'taskqueue_screen_shot_resize', name = 'taskqueue_screen_shot_resize'),
    url(r'^admin/taskqueue/notify-new-app/', 'taskqueue_notify_new_app', name = 'taskqueue_notify_new_app'),
)
    
