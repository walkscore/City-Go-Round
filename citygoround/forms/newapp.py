from decimal import Decimal
from django import forms
from ..models import TransitApp
from ..utils.slug import slugify
from ..utils.misc import uniquify
from ..formfields import AppEngineImageField, AppEngineBlobField, LocationListField, AgencyListField

class NewAppGeneralInfoForm(forms.Form):
    SCREEN_SHOT_COUNT = 5
    SCREEN_SHOT_FIELDS = ('screen_shot', 'screen_shot_2', 'screen_shot_3', 'screen_shot_4', 'screen_shot_5')    
    
    title               = forms.CharField(max_length = 64, min_length = 2, label = u"Title")
    description         = forms.CharField(max_length = 140, min_length = 2, label = u"One Sentence Description")
    url                 = forms.URLField(verify_exists = False, min_length = 2, label = u"App URL")
    price               = forms.DecimalField(decimal_places = 2, max_digits = 6, min_value = Decimal("0.00"), initial = Decimal("0.00"), label = u"Price (USD)")
    author_name         = forms.CharField(max_length = 128, min_length = 2, label = u"Author's Name")
    author_email        = forms.EmailField(label = u"Author's Email (kept private)")
    long_description    = forms.CharField(min_length = 0, max_length = 2048, widget = forms.widgets.Textarea(attrs = {'rows': 6, 'cols': 32}), label = u"Extended Description")
    platforms           = forms.MultipleChoiceField(choices = TransitApp.platform_choices(), widget = forms.widgets.CheckboxSelectMultiple(), label = u"Platforms supported:")
    categories          = forms.MultipleChoiceField(choices = TransitApp.category_choices(), widget = forms.widgets.CheckboxSelectMultiple(), initial=[u"public_transit"], label = u"Categories (choose at least one):")
    tags                = forms.CharField(required = False, max_length = 1024, min_length = 0, label = u"Extra Tags (comma separated)")
    screen_shot         = AppEngineBlobField(required = True, label = u"Screen Shot (required)")
    screen_shot_2       = AppEngineBlobField(required = False, label = u"Screen Shot #2 (optional)")
    screen_shot_3       = AppEngineBlobField(required = False, label = u"Screen Shot #3 (optional)")
    screen_shot_4       = AppEngineBlobField(required = False, label = u"Screen Shot #4 (optional)")
    screen_shot_5       = AppEngineBlobField(required = False, label = u"Screen Shot #5 (optional)")
    
    def clean_title(self):
        if (not self.is_unique_slug) or (self.transit_app_slug == "nearby") or (self.transit_app_slug == "add"):
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
        return uniquify([tag.strip() for tag in self.cleaned_data['tags'].split(',') if tag.strip()!=''] + self.platform_list + self.category_list)
        
    @property
    def platform_list(self):
        return uniquify([TransitApp.PLATFORMS[platform_choice] for platform_choice in self.cleaned_data['platforms']])
        
    @property
    def category_list(self):
        return uniquify([TransitApp.CATEGORIES[category_choice] for category_choice in self.cleaned_data['categories']])        

class NewAppAgencyForm(forms.Form):
    progress_uuid = forms.CharField(required = True, widget = forms.widgets.HiddenInput)
    gtfs_choice = forms.ChoiceField(required = True, choices = TransitApp.gtfs_choices(), widget = forms.widgets.RadioSelect(), label = u"")
    agency_list = AgencyListField(required = False, widget = forms.widgets.HiddenInput)
    
    def clean(self):
        if "gtfs_choice" not in self.cleaned_data:
            raise forms.ValidationError("You must choose one of the options below.")
        if (self.cleaned_data["gtfs_choice"] == "specific_agencies") and (len(self.cleaned_data["agency_list"]) < 1):
            raise forms.ValidationError("Since your application supports data from specific agencies, you must select at least one agency in the list below.")
        return self.cleaned_data
    
class NewAppLocationForm(forms.Form):
    progress_uuid = forms.CharField(required = True, widget = forms.widgets.HiddenInput)
    location_list = LocationListField(required = False, widget = forms.widgets.HiddenInput)
    available_globally = forms.BooleanField(required = False, label = u"Globally", widget = forms.widgets.CheckboxInput(attrs={'id': 'global'}))
