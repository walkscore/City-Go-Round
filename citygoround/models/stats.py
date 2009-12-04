from google.appengine.ext import db

class TransitAppStats(db.Model):
    # low contention model -- don't bother with sharding
    transit_app_count   = db.IntegerProperty()
    
    @staticmethod
    def get_transit_app_stats():
        # A "singleton" datastore entry for now
        stats = TransitAppStats.all().get()
        if stats is None:
            stats = TransitAppStats(transit_app_count = 0)
            try:
                stats.put()
            except db.TimeoutException:
                stats.put()
        return stats
            
    @staticmethod
    def get_transit_app_count():
        return TransitAppStats.get_transit_app_stats().transit_app_count
        
    @staticmethod
    def increment_transit_app_count():
        stats = TransitAppStats.get_transit_app_stats()
        stats.transit_app_count = stats.transit_app_count + 1
        try:
            stats.put()
        except db.TimeoutException:
            stats.put()
    
