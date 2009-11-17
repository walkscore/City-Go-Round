import os

RUNNING_APP_ENGINE_LOCAL_SERVER = os.environ['SERVER_SOFTWARE'].startswith('Dev')

DEBUG = RUNNING_APP_ENGINE_LOCAL_SERVER # For now

APPEND_SLASH = True

INSTALLED_APPS = ['opentransit']

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'opentransit.middleware.SiteWideUsernameAndPassword',
]

# NOTE davepeck:
#
# Add the following two middleware classes
# if you want support for users in this application
# (I wrote these classes myself for another project)
#
# 'opentransit.middleware.AppEngineSecureSessionMiddleware',
# 'opentransit.middleware.AppEngineGenericUserMiddleware',


ROOT_URLCONF = 'urls'

TEMPLATE_CONTEXT_PROCESSORS = ['opentransit.context.api_keys'] 

# NOTE davepeck:
#
# (also add the following context processor if you want user support)
#
# 'opentransit.context.appengine_user'

TEMPLATE_DEBUG = DEBUG

TEMPLATE_DIRS = [os.path.join(os.path.dirname(__file__), 'templates')]

TEMPLATE_LOADERS = ['django.template.loaders.filesystem.load_template_source']

FILE_UPLOAD_HANDLERS = ['django.core.files.uploadhandler.MemoryFileUploadHandler']

FILE_UPLOAD_MAX_MEMORY_SIZE = 1048576 # 1 MB -- an appengine maximum

SERIALIZATION_SECRET_KEY = '\xcfB\xf6\xb9\xc4\xe4\xfa\x07\x8atE\xdc\xec\xf9zaR\xa4\x13\x88'

LOGIN_URL = "/login/"

REDIRECT_FIELD_NAME = "redirect_url"

# Site-Wide HTTP Basic Auth Settings
# (A little absurd since we're open source, but
# casual eyes won't see us 'til we're ready.)
SITE_WIDE_USERNAME = "transit"
SITE_WIDE_PASSWORD = "appsnearyou"
SITE_WIDE_REALM = "Open Transit Data"

#override in local_settings.py, not here
GOOGLE_API_KEY='ABQIAAAAOtgwyX124IX2Zpe7gGhBsxSCRqJWmDzbZh5mozwXpdIfpjWXRhSi9qNJD6bg7_Sl6DjLqkfJ2UmOmA'

# only use local_settings.py if we're running debug server
if RUNNING_APP_ENGINE_LOCAL_SERVER:
    try:
        from local_settings import *
    except ImportError, exp:
        pass

