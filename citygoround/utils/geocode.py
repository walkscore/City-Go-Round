from google.appengine.api.urlfetch import fetch
from django.utils import simplejson as json

def geocode_name(city, state):

    key = "ABQIAAAARFBfEeey0ac5JKru_9nB4BRNy0I-ty1ceBzDzdazMPQQJBF-YBTicqpsbJEKspGxit8ea-iSAtSD9A"
    
    geocoder_url = 'http://maps.google.com/maps/geo?sensor=false&key=%s&q=%s'

    loc = city.replace(' ','%20') + ',%20' +  state
    
    url = geocoder_url % (key, loc)
    
    geo = fetch(url).content

    j = json.loads(geo)
    coords = j['Placemark'][0]['Point']['coordinates']
    
    return "%s,%s"%(coords[1],coords[0])