import urllib2
import csv
import time
try:
    import json
except ImportError:
    import simplejson as json

DELAY = 3
API_KEY = "ABQIAAAARFBfEeey0ac5JKru_9nB4BRNy0I-ty1ceBzDzdazMPQQJBF-YBTicqpsbJEKspGxit8ea-iSAtSD9A"

def geocode_name(city, state, key):
    geocoder_url = 'http://maps.google.com/maps/geo?sensor=false&key=%s&q=%s'

    loc = city.replace(' ','%20') + ',%20' +  state
    
    url = geocoder_url % (key, loc)
    try:
       geo = urllib2.urlopen(url).read()
    except Exception:
       print 'error with %s' % url
       time.sleep(5)
       geo = urllib2.urlopen(geocoder_url % loc).read()

    j = json.loads(geo)
    coords = j['Placemark'][0]['Point']['coordinates']
    
    return coords

if __name__=='__main__':
    #be sure your csv has a "city" and "state" header
    fout = open('agencies_geocoded.csv', 'w')
    out = csv.writer(fout)
    reader =  csv.reader(open('agencies.csv'))
    cols = reader.next()

    ci = cols.index('city')
    si = cols.index('state')

    cols.append('geocoded')
    out.writerow(cols)
    for row in reader:
        
        coords = geocode_name( row[ci], row[si], API_KEY )
        
        print coords

        row.append(str(coords[0]) + ',' + str(coords[1]))
        out.writerow(row)
        print row
        time.sleep(DELAY)
    fout.close()
