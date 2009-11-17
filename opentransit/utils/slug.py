import re
import unicodedata

#from django.utils.encoding import force_unicode

def slugify(value):
    value = unicode(value)
    #value = force_unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub(r'[^\w\s-]', '', value).strip().lower())
    value = re.sub(r'[-\s]+', '-', value)
    return value
