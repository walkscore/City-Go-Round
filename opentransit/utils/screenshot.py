from google.appengine.ext import db

from .image import crop_and_resize_image_to_square, convert_image
from ..models import TransitApp, ImageBlob

def get_family_and_screen_shot_blobs(image_bytes):
    """Create screen shot blobs of appropriate sizes for the given image. Returns the name of an image family, and a list of ImageBlob objects belonging to that family."""
    family = None
    blobs = []
    for name, (width, height) in TransitApp.SCREEN_SHOT_NAME_TO_SIZE:
        if family is None:
            blob = ImageBlob.new_with_unique_family()
            family = blob.family
            attempt_image = convert_image(image_bytes) # defaults to PNG
        else:
            blob = ImageBlob(family = family)
            attempt_image = crop_and_resize_image_to_square(image_bytes, width, height) # defaults to PNG
        if attempt_image is not None:
            blob.image = db.Blob(attempt_image)
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
            if inner_blobs:
                families.append(family)
                blobs.extend(inner_blobs)
    return (families, blobs)


