import urllib2
import csv
import time
import json


geocoder_url = 'http://maps.google.com/maps/geo?sensor=false&key=ABQIAAAARFBfEeey0ac5JKru_9nB4BRNy0I-ty1ceBzDzdazMPQQJBF-YBTicqpsbJEKspGxit8ea-iSAtSD9A&q=%s'

out = csv.writer(open('agencies_geocoded.csv', 'w'))
reader =  csv.reader(open('agencies.csv'))
cols = reader.next()
print cols
for r in reader:
    loc = ', '.join(r[2:3])
    geo = urllib2.urlopen(geocoder_url % loc).read()
    j = json.loads(geo)
    coords = j['Placemark'][0]['Point']['coordinates']
    r[9] = str(coords[0]) + ',' + str(coords[1])
    out.writerow(r)
    print r
    time.sleep(3)
out.close()
