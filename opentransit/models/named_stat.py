from google.appengine.ext import db

class NamedStat(db.Model):
    # low contention model -- don't bother with sharding
    name  = db.StringProperty()
    value = db.FloatProperty()
    
    @staticmethod
    def get_stat(name):
        # A "singleton" datastore entry for now
        stats = NamedStat.all().filter("name =",name).get()
        if stats is None:
            stats = NamedStat(name=name, value=0.0)
            try:
                stats.put()
            except db.TimeoutException:
                stats.put()
        return stats
            
    @staticmethod
    def get_value(name):
        return NamedStat.get_stat(name).value
        
    @staticmethod
    def set_value(name,value):
        stats = NamedStat.get_stat(name)
        stats.value = value
        stats.put()
        
    @staticmethod
    def increment(name):
        stats = NamedStat.get_stat(name)
        stats.value = stats.value + 1.0
        try:
            stats.put()
        except db.TimeoutException:
            stats.put()
        return stats.value
