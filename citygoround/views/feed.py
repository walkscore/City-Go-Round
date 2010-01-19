import time
import logging
from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.api.urlfetch import fetch as fetch_url
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..utils.mailer import send_to_contact
from ..utils.prettyprint import pretty_print_time_elapsed
from ..models import FeedReference, Agency
from urlparse import urlparse
import re
from datetime import datetime
from django.http import HttpResponse

def id_from_gtfs_data_exchange_url(url):
    return re.findall( "/agency/(.*)/", urlparse( url )[2] )[0]
    
def delete_feed_references(old_references):
    # TODO: deleting one at a time is stupid
    # delete all current references
    for feed_reference in old_references:
        feed_reference.delete()
        
def add_new_references( new_references ):
    # keep correspondance of gtfs_data_exchange_ids to is_officialness
    gtfs_is_official = {}
    
    # add all the new references
    parentKey = db.Key.from_path("FeedReference", "base")
    for feed_reference_json in new_references:
        fr = FeedReference(parent=parentKey)
        
        fr.date_last_updated = datetime.fromtimestamp( feed_reference_json['date_last_updated'] )
        fr.feed_baseurl      = feed_reference_json['feed_baseurl'].strip() if feed_reference_json['feed_baseurl'] != "" else None
        fr.name              = feed_reference_json['name']
        fr.area              = feed_reference_json['area']
        fr.url               = feed_reference_json['url'].strip()
        fr.country           = feed_reference_json['country']
        fr.dataexchange_url  = feed_reference_json['dataexchange_url'].strip()
        fr.state             = feed_reference_json['state']
        fr.license_url       = feed_reference_json['license_url'].strip() if feed_reference_json['license_url'] != "" else None
        fr.date_added        = datetime.fromtimestamp( feed_reference_json['date_added'] )
        fr.is_official       = feed_reference_json.get('is_official', True) # is_official is True by default
        
        # be hopeful that the api call has the external id. If not, yank it from the url
        if 'external_id' in feed_reference_json:
            fr.gtfs_data_exchange_id = feed_reference_json['external_id']
        else:
            fr.gtfs_data_exchange_id = id_from_gtfs_data_exchange_url( fr.dataexchange_url )
        
        fr.put()
        
        # mark the date_opened of the feed, for flipping the agency open bit later
        if fr.is_official:
            gtfs_is_official[fr.gtfs_data_exchange_id] = fr.date_added
            
    return gtfs_is_official
    
def set_agency_date_added( gtfs_is_official ):
    # flip the date_added prop for every agency
    # for each agency
    for agency in Agency.all():
        
        date_agency_opened = None
        
        # for every gtfs data exchange page for this agency
        for gtfs_data_exchange_id in agency.gtfs_data_exchange_id:
            date_feed_opened = gtfs_is_official.get(gtfs_data_exchange_id)
            
            # if the feed is open, and before the current date_agency_opened
            if date_feed_opened is not None and (date_agency_opened is None or date_feed_opened < date_agency_opened):
                date_agency_opened = date_feed_opened
                
        # the date the agency opened is the date the earliest feed opened
        agency.date_opened = date_agency_opened
        
        # only update the agency if you did something to it
        if date_agency_opened is not None:
            agency.put()

def update_feed_references(request):
    try:
        FEED_REFS_URL = "http://www.gtfs-data-exchange.com/api/agencies"
        
        # grab feed references and load into json
        feed_refs_json = json.loads( fetch_url( FEED_REFS_URL ).content )['data']
        
        # replace feed references in a transaction
        old_references = FeedReference.all().fetch(1000)
        
        if request.GET.get( "delete" ) != "false":
            # delete old references
            delete_feed_references(old_references)
        
        if request.GET.get( "add" ) != "false":
            # add new references
            gtfs_is_official = add_new_references( feed_refs_json )
        
        if request.GET.get( "sync" ) != "false":
            # set the official flag on every agency that's official
            set_agency_date_added( gtfs_is_official )
        
        send_to_contact( "Cron job ran successfully", "Cron job ran successfully at %s"%time.time(), "badhill@gmail.com" )
          
        # redirect to a page for viewing all your new feed references
        return redirect_to("admin_feed_references")
    except Exception, e:
        send_to_contact( "Cron job messed up", "The Update Feeds cron job messed up: %s at %s"%(e, time.time()), "badhill@gmail.com" )
        raise
    
def admin_feed_references(request):
    all_references = FeedReference.all().order("-date_added")
    
    refs_with_elapsed = []
    present_moment = datetime.now()
    for ref in all_references:
        refs_with_elapsed.append( {'ref':ref, 'ago':str(present_moment-ref.date_added), 'date_added':ref.date_added} )
    
    return render_to_response( request, "feed_references.html", {'all_references':refs_with_elapsed} )
    

    