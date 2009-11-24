from google.appengine.ext import db

from .image import crop_and_resize_image, convert_image
from ..models import TransitApp, ImageBlob

def get_family_and_screen_shot_blobs(image_bytes):
    """Create screen shot blobs of appropriate sizes for the given image. Returns the name of an image family, and a list of ImageBlob objects belonging to that family."""
    # Validate the bytes and make them PNG at the same time (PNG is default to convert_image)
    png_bytes = convert_image(image_bytes)
    if not png_bytes:
        return (None, [])
    
    # Set up our "original sized" image -- (0, 0) is the "original size"
    original_blob = ImageBlob.new_with_unique_family()
    original_blob.image = db.Blob(png_bytes)
    original_blob.width = 0
    original_blob.height = 0
    original_blob.extension = "png"

    # Now handle the rest of the image sizes
    blobs = [original_blob]
    family = original_blob.family    
    for name, (width, height) in TransitApp.SCREEN_SHOT_SIZES:
        if (width != 0) or (height != 0):
            blob = ImageBlob(family = family)
            blob.image = db.Blob(crop_and_resize_image(image_bytes, width, height)) # defaults to PNG
            blob.width = width
            blob.height = height
            blob.extension = "png"
            blobs.append(blob)
    return (family, blobs)

def get_families_and_screen_shot_blobs(image_bytes_list):
    """Helper to append a list of screen shots. Returns a list of ImageBlob objects that must be put()."""
    families = []
    blobs = []
    for image_bytes in image_bytes_list:
        if image_bytes is not None:
            family, inner_blobs = get_family_and_screen_shot_blobs(image_bytes)
            if family and inner_blobs:
                families.append(family)
                blobs.extend(inner_blobs)
    return (families, blobs)


