import urllib2
import csv
import time
import json

#be sure your csv has a "city" and "state" header

geocoder_url = 'http://maps.google.com/maps/geo?sensor=false&key=ABQIAAAARFBfEeey0ac5JKru_9nB4BRNy0I-ty1ceBzDzdazMPQQJBF-YBTicqpsbJEKspGxit8ea-iSAtSD9A&q=%s'

fout = open('agencies_geocoded.csv', 'w')
out = csv.writer(fout)
reader =  csv.reader(open('agencies.csv'))
cols = reader.next()

ci = cols.index('city')
si = cols.index('state')

cols.append('geocoded')
out.writerow(cols)
for r in reader:
    loc = r[ci].replace(' ','%20') + ',%20' +  r[si]
    url = geocoder_url % loc
    try:
       geo = urllib2.urlopen(url).read()
    except:
       print 'error with %s' % url
       time.sleep(5)
       geo = urllib2.urlopen(geocoder_url % loc).read()

    j = json.loads(geo)
    coords = j['Placemark'][0]['Point']['coordinates']
    r.append(str(coords[0]) + ',' + str(coords[1]))
    out.writerow(r)
    print r
    time.sleep(3)
fout.close()
