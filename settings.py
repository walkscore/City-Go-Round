import os

RUNNING_APP_ENGINE_LOCAL_SERVER = os.environ.get('SERVER_SOFTWARE', 'Dev').startswith('Dev')

DEBUG = RUNNING_APP_ENGINE_LOCAL_SERVER # For now

S3_URL_ROOT = "http://files.citygoround.org.s3.amazonaws.com"

APPEND_SLASH = True

INSTALLED_APPS = ['citygoround', 'gaeunit']

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'citygoround.middleware.AppEngineSecureSessionMiddleware',
]

DEBUG_SESSIONS = False # Set to True to get log lines about the contents of the session object

SITE_WIDE_USERNAME_AND_PASSWORD_URL_EXCEPTIONS = [ r'^/admin/taskqueue/.*$' ]

# NOTE davepeck:
#
# Add the following middleware classes
# if you want support for users in this application
# (I wrote these classes myself for another project)
#
# 'citygoround.middleware.AppEngineGenericUserMiddleware',


ROOT_URLCONF = 'urls'

TEMPLATE_CONTEXT_PROCESSORS = ['citygoround.context.api_keys'] 

# NOTE davepeck:
#
# (also add the following context processor if you want user support)
#
# 'citygoround.context.appengine_user'

TEMPLATE_DEBUG = DEBUG

TEMPLATE_DIRS = [os.path.join(os.path.dirname(__file__), 'templates')]

TEMPLATE_LOADERS = ['django.template.loaders.filesystem.load_template_source']

# FILE_UPLOAD_HANDLERS = ['django.core.files.uploadhandler.MemoryFileUploadHandler']
FILE_UPLOAD_HANDLERS = ['citygoround.uploadhandlers.AppEngineBlobUploadHandler']

FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760 # 10 MB -- an appengine maximum
MAX_IMAGE_SIZE = 983040  # 960 KB per image -- slightly under 1MB to guard against issues with db.put()

SERIALIZATION_SECRET_KEY = '\xcfB\xf6\xb9\xc4\xe4\xfa\x07\x8atE\xdc\xec\xf9zaR\xa4\x13\x88'

MEMCACHE_DEFAULT_SECONDS = 60 * 60
MEMCACHE_PAGE_SECONDS = MEMCACHE_DEFAULT_SECONDS
MEMCACHE_API_SECONDS = 24 * 60 * 60
MEMCACHE_SCREENSHOT_SECONDS = MEMCACHE_DEFAULT_SECONDS
MEMCACHE_SCREENSHOT_MAX_SIZE = 65536 # empirically, 64kb is a good max size for caching screen shots. This covers all the gallery page and home page screen shots.

DEFAULT_TRANSIT_APP_IMAGE_URL = "/images/default-transit-app.png"
DEFAULT_TRANSIT_APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'citygoround/images/'))
DEFAULT_TRANSIT_APP_BASE = DEFAULT_TRANSIT_APP_PATH + "/default-transit-app"
DEFAULT_TRANSIT_APP_EXTENSION = "png"


LOGIN_URL = "/login/"

REDIRECT_FIELD_NAME = "redirect_url"

# Site-Wide HTTP Basic Auth Settings
# (A little absurd since we're open source, but
# casual eyes won't see us 'til we're ready.)
SITE_WIDE_USERNAME = "transit"
SITE_WIDE_PASSWORD = "appsnearyou"
SITE_WIDE_REALM = "City Go Round"

TRANSIT_APP_IMAGE_WIDTH = 180
TRANSIT_APP_IMAGE_HEIGHT = 180

#override in local_settings.py, not here
GOOGLE_API_KEY='ABQIAAAAOtgwyX124IX2Zpe7gGhBsxScRvQHjv9UbfX2QLoR8lJzqlEEMhQOYVWJMRvlY9Hz-bSACEukjIPCWA'

BBOX_SIDE_IN_MILES = 50.0 #like a search radius of 25 miles
NEARBY_AGENCIES_BBOX_SIDE_IN_MILES = 50.0 #like a search radius of 25 miles

if DEBUG:
    PROGRESS_DEBUG_MAGIC = "DEBUG"
else:
    PROGRESS_DEBUG_MAGIC = None

# only use local_settings.py if we're running debug server
if RUNNING_APP_ENGINE_LOCAL_SERVER:
    try:
        from local_settings import *
    except ImportError, exp:
        pass

NEW_APP_EMAIL_RECIPIENTS = ["badhill@gmail.com", 
                            "davepeck@davepeck.org",
                            "jesse@frontseat.org",
                            "matt@frontseat.org",
                            "aleisha@frontseat.org"]
