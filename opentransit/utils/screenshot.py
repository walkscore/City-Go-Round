import logging
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue

from django.core.urlresolvers import reverse

from .image import crop_and_resize_image, convert_image
from ..models import TransitApp, ImageBlob

def create_original_screen_shot_blob(image_bytes):
    """Return a single ImageBlob, with unique family name, for this image."""
    # Validate the bytes and make them PNG at the same time (PNG is the default to convert_image)
    png_bytes = convert_image(image_bytes)
    if not png_bytes: return None
    
    # Set up our original sized image -- (0, 0) is "orginal size"
    original_blob = ImageBlob.new_with_unique_family()
    original_blob.image = db.Blob(png_bytes)
    original_blob.width = 0
    original_blob.height = 0
    original_blob.extension = "png"
    return original_blob
    
def create_and_store_original_screen_shot_blob(image_bytes):
    """Create an original screen shot blob and add it to the data store. Return the family ID for future reference."""
    blob = create_original_screen_shot_blob(image_bytes)
    if not blob: return None
    db.put(blob) # TODO davepeck: error handling!!!
    return blob.family
    
def create_and_store_screen_shot_blob_for_family(family, width, height):
    original_blob = ImageBlob.get_original_for_family(family)
    if not original_blob:
        raise Error("Could not find the original image blob for family %s. Fail." % family)
    
    resized_blob = ImageBlob(family = family)
    resized_blob.image = db.Blob(crop_and_resize_image(original_blob.image, width, height)) # defaults to PNG
    resized_blob.width = width
    resized_blob.height = height
    resized_blob.extension = "png"
    resized_blob.put()
    
def kick_off_resizing_for_screen_shot(image_bytes):
    """Create and store the original screen shot, and queue up tasks to perform all other resizings."""
    family = create_and_store_original_screen_shot_blob(image_bytes)
    if family is None: return None
    
    for name, (width, height) in TransitApp.SCREEN_SHOT_SIZES:
        if (width != 0) or (height != 0):
            task = taskqueue.Task(
                url = reverse("taskqueue_screen_shot_resize"),
                name = "resize-%s-%s" % (family, name),
                params = {
                    "family": family,
                    "name": name,
                    "width": width,
                    "height": height,
                },
            )
            task.add(queue_name = "screen-shot-resize-queue")
            
    return family

def kick_off_resizing_for_screen_shots(image_bytes_list):
    """Create and store the original screen shots for each image in the list, and queue up tasks to perform all other resizings."""
    families = []
    for image_bytes in image_bytes_list:
        if image_bytes is not None:
            family = kick_off_resizing_for_screen_shot(image_bytes)
            if family is not None:
                families.append(family)
    return families
