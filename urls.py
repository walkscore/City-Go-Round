# NOTE: Must import *, since Django looks for things here, e.g. handler500.
from django.conf.urls.defaults import *

# Load the opentransit application's URLs
urlpatterns = patterns('', url(r'', include('opentransit.urls')))
