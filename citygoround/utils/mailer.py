import logging
import time
from google.appengine.api import mail, memcache
from google.appengine.api.labs import taskqueue
from google.appengine.runtime.apiproxy_errors import OverQuotaError

from django.core.urlresolvers import reverse

import sys
import traceback

def _typename(t):
    """helper function -- isolates the type name from the type string"""
    if t:
        return str(t).split("'")[1]
    else:
        return "{type: None}"

def _typeof(thing):
    """Get the type name, such as str, float, or int"""
    return _typename(type(thing))

def exception_string():
    """called to extract useful information from an exception"""
    exc = sys.exc_info()
    exc_type = _typename(exc[0])
    exc_message = str(exc[1])
    exc_contents = "".join(traceback.format_exception(*sys.exc_info()))
    return "[%s]\n %s" % (exc_type, exc_contents)

"""
Mail functions:
Used to mail API users and administrators regarding errors, reports, etc.
Contains core mail functions, plus convenience functions for common cases
"""

def send_to_contact(subject, body, recipient="jesse@frontseat.org"):
    message = mail.EmailMessage(sender="no-reply@citygoround.org")
    message.to = recipient
    logging.info("MAIL: %s :: %s" % (subject, body))
    message.subject = subject
    message.body = body
    try:
        message.send()
    except OverQuotaError:
        exc_str = exception_string()
        logging.error("Over Quota:  failed to send mail: %s\n%s" % (subject, exc_str))
    except:
        exc_str = exception_string()
        logging.error("Unknown error: failed to send mail: %s\n%s" % (subject, exc_str))
    return  

"""
New app email notification taskqueue function
"""

def kick_off_new_app_notification(transit_app):
    task = taskqueue.Task(
        url = reverse("taskqueue_notify_new_app"),
        name = "notify-transit-app-%s" % (transit_app.key().id()),
        params = {
            "id": transit_app.key().id(),
            "title": transit_app.title,
            "url": transit_app.details_url,
        },
    )
    task.add(queue_name = "notify-new-app-queue")

"""
throttle_mail Returns True if a mail with this subject HAS been sent in the last 
five minutes.  
Returns False if it has NOT been sent (I know, it's poorly named)
"""

"""
def throttle_mail(subject):
    # Using memcache is potentially weak if you want exactly no more than X emails every 300 seconds
    mkey = 'mail_cache_time_' + subject
    last_time = memcache.get(mkey)
    if not last_time:
        memcache.set(mkey, time.time())
        return False
    if time.time() - last_time <= 300:
        return True
    memcache.set(mkey, time.time())     
    return False  

def send_to_admin(subject, body):
    if throttle_mail(subject):
        logging.debug('already sent out an email titled %s in the last 5 mins' % subject)
        return
    message = mail.EmailMessage(sender="info@citygoround.org")
    message.to = "api-error@frontseat.org"
    message.subject = subject
    message.body = body
    try:
        message.send()
    except OverQuotaError:
        exc_str = exception_string()
        logging.error("Over Quota:  failed to send mail: %s\n%s" % (subject, exc_str))
    except:
        exc_str = exception_string()
        logging.error("Unknown error: failed to send mail: %s\n%s" % (subject, exc_str))
    return  
"""

