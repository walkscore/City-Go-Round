from .memcache import clear_all_apps
from ..models import NamedStat

def rating_key_for_app(transit_app):
    return "rating-%s" % transit_app.slug

def get_user_rating_for_app(request, transit_app):
    key = rating_key_for_app(transit_app)
    return request.get_session(key, None)

def set_user_rating_for_app(request, transit_app, rating):
    key = rating_key_for_app(transit_app)
    return request.set_session(key, rating)

def adjust_rating_for_app(transit_app, old_rating, new_rating):
    # Remember the original integer rating for the app
    original_rating = transit_app.average_rating_integer
    
    # Determine what to adjust the app by
    if old_rating is not None:
        if new_rating is not None:
            rating_delta = new_rating - old_rating
            count_delta = 0
        else:
            rating_delta = -old_rating
            count_delta = -1
    else:
        rating_delta = new_rating if new_rating is not None else 0
        count_delta = 1
    
    # Set side-wide rating average for use in creating sorting metric using bayesian average
    all_rating_sum = NamedStat.get_stat( "all_rating_sum" )
    all_rating_sum.value = all_rating_sum.value + rating_delta
    all_rating_sum.put()
    
    all_rating_count = NamedStat.get_stat( "all_rating_count" )
    all_rating_count.value = all_rating_count.value + count_delta
    all_rating_count.put()
    
    # Fix the app's raw rating info
    transit_app.rating_sum += rating_delta
    transit_app.rating_count += count_delta
    
    # Refresh the app's bayesian average
    transit_app.refresh_bayesian_average(all_rating_sum, all_rating_count)    
    transit_app.put()
    
    # Now see if we should clear the memcache for the app gallery and apps APIs.
    # we _will_ if this was a first rating, or if the overall rating changed by
    # enough. Otherwise, we'll wait for our memcache expiry time to arrive.
    final_rating = transit_app.average_rating_integer
    if (original_rating == 0) or (abs(original_rating - final_rating) >= 5):
        clear_all_apps()
    