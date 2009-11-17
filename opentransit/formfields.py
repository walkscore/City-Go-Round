from django import forms
from google.appengine.api import images
from django.utils.translation import ugettext_lazy as _
from .utils.image import image_bytes_are_valid

# Django's built-in ImageField doesn't work on AppEngine because
# it relies on unavailable PIL APIs. Here's my own version that works.

class AppEngineImageField(forms.FileField):
    default_error_messages = {
        'invalid_image': _(u"Upload a valid image. The file you uploaded was either not an image or was a corrupted image."),
    }
    
    def clean(self, data, initial=None):
        raw_file = super(AppEngineImageField, self).clean(data, initial)
        if raw_file is None:
            return None
        elif not data and initial:
            return initial
            
        if hasattr(data, 'read'):
            bytes = data.read()
        else:
            try:
                bytes = data['content']
            except:
                bytes = None
        
        if bytes is None:
            raise forms.ValidationError(self.error_messages['invalid_image'])
        
        if (len(bytes) > 0) and (not image_bytes_are_valid(bytes)):
            raise forms.ValidationError(self.error_messages['invalid_image'])
        
        if hasattr(raw_file, 'seek') and callable(raw_file.seek):
            raw_file.seek(0)
            
        return raw_file
        
                
                