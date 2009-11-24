from uuid import uuid4

from google.appengine.ext import db
from google.appengine.api import images

class ImageBlob(db.Model):
    ORIGINAL_SIZE = (0, 0)
    
    # Image entities are unique across family+width+height
    # All images with the same "family" have the same effective image, but may have different width/height        
    image = db.BlobProperty()
    family = db.StringProperty(required = True, indexed = True)
    width = db.IntegerProperty(required = True, indexed = True)
    height = db.IntegerProperty(required = True, indexed = True)
    extension = db.StringProperty()

    @staticmethod
    def new_with_unique_family():
        return Image(family = str(uuid4()).replace('-', ''))
    
    @staticmethod
    def all_in_family(family):
        return Image.all().filter('family =', family)
        
    @staticmethod
    def get_for_family_and_size(family, (width, height)):
        return Image.all().filter('family =', family).filter('width =', width).filter('height =', height).get()

    @staticmethod
    def get_bytes_and_extension_for_family_and_size(family, (width, height)):
        blob = self.get_for_family_and_size(family, (width, height))
        if not blob: return (None, None)
        return (blob.image, blob.extension)

        
        
