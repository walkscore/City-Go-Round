import logging
from google.appengine.api import images

def image_bytes_are_valid(image_bytes):
    try:
        test_image = images.Image(image_bytes)
        # Unfortunately the only way to validate image bytes on AppEngine is to
        # perform a transform. Lame. ALSO: the latest version of PIL on OSX (needed
        # only for running dev_appserver locally) requires at least one transformation
        # in the pipeline, or execute_transforms will fail. So... fix that, too.
        test_image.crop(0.0, 0.0, 1.0, 1.0)
        ignored_output = test_image.execute_transforms(images.PNG)
    except images.Error:
        return False
    return True

def convert_image(image_bytes, output_encoding=images.PNG):
    try:
        test_image = images.Image(image_bytes)
        # Unfortunately the only way to validate image bytes on AppEngine is to
        # perform a transform. Lame. ALSO: the latest version of PIL on OSX (needed
        # only for running dev_appserver locally) requires at least one transformation
        # in the pipeline, or execute_transforms will fail. So... fix that, too.
        test_image.crop(0.0, 0.0, 1.0, 1.0)
        converted_bytes = test_image.execute_transforms(images.PNG)
    except images.Error:
        return None
    return converted_bytes

def crop_and_resize_image(image_bytes, final_width, final_height, output_encoding=images.PNG):
    try:
        original_image = images.Image(image_bytes)
        original_width, original_height = original_image.width, original_image.height

        # If one dimension is unspecified, we simply resize the image...
        if (final_width == 0) or (final_height == 0):
            if final_width:
                original_image.resize(width = final_width)
            elif final_height:
                original_image.resize(height = final_height)
            else:
                raise Exception("You must specify at least one resize dimension.")
                
        # But if both dimensions are specified, we resize and crop...
        else:
            if final_width != final_height:
                raise Exception("TODO davepeck: when and if we need it, support non-square crops")
                
            # Is the image square?
            if original_width != original_height:
                # No, so force it to be a square (cut off the long direction)
                if original_width < original_height:
                    original_image.crop(0.0, 0.0, 1.0, float(original_width) / float(original_height))
                else:
                    original_image.crop(0.0, 0.0, float(original_height) / float(original_width), 1.0)
        
            # Force the image to final desired size
            original_image.resize(width = final_width, height = final_height)

        # Get final bytes
        resized_bytes = original_image.execute_transforms(output_encoding)
    except images.Error:
        resized_bytes = None
        
    return resized_bytes
