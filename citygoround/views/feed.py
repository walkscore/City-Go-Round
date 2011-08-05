import time
import logging
from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.api.urlfetch import fetch as fetch_url
from google.appengine.api.datastore_errors import BadValueError
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

def gtfs_data_exchange_id_from_feed_reference_json( feed_reference_json ):
    # be hopeful that the api call has the external id. If not, yank it from the url
    if 'dataexchange_id' in feed_reference_json:
        return feed_reference_json['dataexchange_id']
    else:
        return id_from_gtfs_data_exchange_url( feed_reference_json['dataexchange_url'].strip() )

def new_feed_reference_from_json( feed_reference_json, parentKey ):
    fr = FeedReference(parent=parentKey)
    
    fr.date_last_updated = feed_reference_json['date_last_updated']
    fr.feed_baseurl      = feed_reference_json['feed_baseurl'].strip() if feed_reference_json['feed_baseurl'] != "" else None
    fr.name              = feed_reference_json['name']
    fr.area              = feed_reference_json['area']
    try:
        fr.url               = feed_reference_json['url'].strip()
    except BadValueError, e:
        logging.error ("Invalid url %s, setting to None" % feed_reference_json['url'])
        fr.url           = None
    fr.country           = feed_reference_json['country']
    fr.dataexchange_url  = feed_reference_json['dataexchange_url'].strip()
    fr.state             = feed_reference_json['state']
    fr.license_url       = feed_reference_json['license_url'].strip() if feed_reference_json['license_url'] != "" else None
    fr.date_added        = datetime.fromtimestamp( feed_reference_json['date_added'] )
    fr.is_official       = feed_reference_json.get('is_official', True) # is_official is True by default
    
    fr.gtfs_data_exchange_id = gtfs_data_exchange_id_from_feed_reference_json( feed_reference_json )
            
    return fr
        
def update_references( new_references ):
    
    # snag all the old feed references so we can efficiently refer to them
    old_feed_references = {}
    for feed_reference in FeedReference.all():
        old_feed_references[ feed_reference.gtfs_data_exchange_id ] = feed_reference
    
    # add new and updated references
    parentKey = db.Key.from_path("FeedReference", "base")
    for feed_reference_json in new_references:
        external_id = gtfs_data_exchange_id_from_feed_reference_json( feed_reference_json )

        if external_id == "":
            # Just skip this feed
            logging.error("Had trouble processing this feed reference: %s" % feed_reference_json)
            continue
        
        # if the incoming feed reference isn't already around, add it
        if external_id not in old_feed_references:
            logging.info( "adding new feed reference '%s' (last updated %s)"%(external_id, feed_reference_json['date_last_updated']) )

            fr = new_feed_reference_from_json( feed_reference_json, parentKey )
            fr.put()

            
        # if the incoming feed reference already exists, and has been updated recently, replace it
        elif (feed_reference_json['date_last_updated'] > old_feed_references[external_id].date_last_updated) or \
	     (feed_reference_json['is_official'] != old_feed_references[external_id].is_official):
            logging.info( "replacing outdated feed reference '%s' (old: %s new: %s)"%(external_id, 
                                                                                      old_feed_references[external_id].date_last_updated,
                                                                                      feed_reference_json['date_last_updated'] )                                                                                      )
            
            old_feed_references[external_id].delete()
            fr = new_feed_reference_from_json( feed_reference_json, parentKey )
            fr.put()
            
def sync_agency_date_added( ):
    # snag all the old feed references so we can efficiently refer to them
    feed_references = {}
    for feed_reference in FeedReference.all():
        feed_references[ feed_reference.gtfs_data_exchange_id ] = feed_reference
    
    # flip the date_added prop for every agency
    # for each agency
    for agency in Agency.all():
        
        date_agency_opened = None
        
        # for every associated feed reference for this agency
        for gtfs_data_exchange_id in agency.gtfs_data_exchange_id:
            feed_reference = feed_references.get( gtfs_data_exchange_id )
            
            if feed_reference is None:
                continue
                
            date_feed_opened = feed_reference.date_added
            
            # if the feed is open, and before the current date_agency_opened
            if date_feed_opened is not None \
               and (date_agency_opened is None or date_feed_opened < date_agency_opened) \
               and feed_reference.is_official:
                date_agency_opened = date_feed_opened
                
        # only update the agency if we're making a change
        if agency.date_opened != date_agency_opened:
            
            # the date the agency opened is the date the earliest feed opened
            agency.date_opened = date_agency_opened
            agency.put()
            
def delete_all_feed_references(request):
    for feed_reference in FeedReference.all():
        feed_reference.delete()
        
    return redirect_to("admin_feed_references")

def update_feed_references(request):
    try:
        FEED_REFS_URL = "http://gtfs-data-exchange.appspot.com/api/agencies"
        
        # grab feed references and load into json
        feed_refs_json = json.loads( fetch_url( FEED_REFS_URL ).content )['data']
        
        if request.GET.get( "add" ) != "false":
            # add new references
            update_references( feed_refs_json )
            
        if request.GET.get( "sync" ) != "false":
            # set the official flag on every agency that's official
            sync_agency_date_added()
        
        send_to_contact( "Cron job ran successfully", "Cron job ran successfully at %s"%time.time(), "badhill@gmail.com" )
          
        # redirect to a page for viewing all your new feed references
        return HttpResponse("success")
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
    

    
