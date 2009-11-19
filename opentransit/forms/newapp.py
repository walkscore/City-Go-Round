from django import forms
from ..models import TransitApp
from ..utils.slug import slugify
from ..formfields import AppEngineImageField, LocationListField, AgencyListField

class NewAppGeneralInfoForm(forms.Form):
    title               = forms.CharField(max_length = 64, min_length = 6, label = u"Title")
    description         = forms.CharField(max_length = 140, min_length = 6, label = u"One Sentence Description")
    url                 = forms.URLField(verify_exists = False, min_length = 6, label = u"App URL")
    author_name         = forms.CharField(max_length = 128, min_length = 6, label = u"Author's Name")
    author_email        = forms.EmailField(label = u"Author's Email (kept private)")
    long_description    = forms.CharField(min_length = 0, max_length = 2048, widget = forms.widgets.Textarea(attrs = {'rows': 6, 'cols': 32}), label = u"Extended Description")
    tags                = forms.CharField(max_length = 256, min_length = 0, label = u"Tags (comma separated)")
    screen_shot         = AppEngineImageField(required = False, label = u"Screen Shot (optional)")
    
    def clean_title(self):
        if not self.is_unique_slug:
            raise forms.ValidationError("This application title is already in use. Pick a new title.")
        return self.cleaned_data['title']
    
    @property
    def transit_app_slug(self):
        return slugify(self.cleaned_data['title'])
            
    @property
    def is_unique_slug(self):
        return not TransitApp.has_transit_app_for_slug(self.transit_app_slug)
        
    @property
    def tag_list(self):
        return [tag.strip() for tag in self.cleaned_data['tags'].split(',')]


class NewAppAgencyForm(forms.Form):
    pass
    
class NewAppLocationForm(forms.Form):
    pass