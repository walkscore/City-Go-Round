from decimal import Decimal
from django import forms
from ..models import TransitApp
from ..utils.slug import slugify
from ..utils.misc import uniquify
from ..formfields import AppEngineImageField, LocationListField, AgencyListField

class EditAppGeneralInfoForm(forms.Form):
    original_slug       = forms.CharField(required = True, widget = forms.widgets.HiddenInput)
    title               = forms.CharField(max_length = 64, min_length = 2, label = u"Title")
    is_featured         = forms.BooleanField(required = False)
    is_hidden           = forms.BooleanField(required = False)
    description         = forms.CharField(max_length = 140, min_length = 2, label = u"One Sentence Description")
    url                 = forms.URLField(verify_exists = False, min_length = 2, label = u"App URL")
    price               = forms.DecimalField(decimal_places = 2, max_digits = 6, min_value = Decimal("0.00"), initial = Decimal("0.00"), label = u"Price (USD)")
    author_name         = forms.CharField(max_length = 128, min_length = 2, label = u"Author's Name")
    author_email        = forms.EmailField(label = u"Author's Email (kept private)")
    long_description    = forms.CharField(min_length = 0, max_length = 2048, widget = forms.widgets.Textarea(attrs = {'rows': 6, 'cols': 32}), label = u"Extended Description")
    platforms           = forms.MultipleChoiceField(choices = TransitApp.platform_choices(), widget = forms.widgets.CheckboxSelectMultiple(), label = u"Platforms supported:")
    categories          = forms.MultipleChoiceField(choices = TransitApp.category_choices(), widget = forms.widgets.CheckboxSelectMultiple(), initial=[u"public_transit"], label = u"Categories (choose at least one):")
    tags                = forms.CharField(required = False, max_length = 1024, min_length = 0, label = u"Extra Tags (comma separated)")    
    
    def clean_title(self):
        if not self.is_unique_slug:
            if self.transit_app_slug != self.cleaned_data["original_slug"]:
                raise forms.ValidationError("This application title is already in use. Pick a new title.")
        if (self.transit_app_slug == "nearby") or (self.transit_app_slug == "add"):
            raise forms.ValidationError("The names 'nearby' and 'add' are reserved and cannot be used by an application.")
        return self.cleaned_data['title']
    
    @property
    def transit_app_slug(self):
        return slugify(self.cleaned_data['title'])
            
    @property
    def is_unique_slug(self):
        return not TransitApp.has_transit_app_for_slug(self.transit_app_slug)
        
    @property
    def tag_list(self):
        return uniquify([tag.strip() for tag in self.cleaned_data['tags'].split(',')] + self.platform_list + self.category_list)
        
    @property
    def platform_list(self):
        return uniquify([TransitApp.PLATFORMS[platform_choice] for platform_choice in self.cleaned_data['platforms']])
        
    @property
    def category_list(self):
        return uniquify([TransitApp.CATEGORIES[category_choice] for category_choice in self.cleaned_data['categories']])        

class EditAppAgencyForm(forms.Form):
    gtfs_choice = forms.ChoiceField(choices = TransitApp.gtfs_choices(), widget = forms.widgets.RadioSelect(), label = u"", initial = "nothing")
    agency_list = AgencyListField(required = False, widget = forms.widgets.HiddenInput)

class EditAppLocationForm(forms.Form):
    location_list = LocationListField(required = False, widget = forms.widgets.HiddenInput)
    available_globally = forms.BooleanField(required = False, label = u"Globally", widget = forms.widgets.CheckboxInput(attrs={'id': 'global'}))

class EditAppImagesForm(forms.Form):
    SCREEN_SHOT_COUNT = 5
    SCREEN_SHOT_FIELDS = ('new_shot_1', 'new_shot_2', 'new_shot_3', 'new_shot_4', 'new_shot_5')
    
    new_shot_1 = AppEngineImageField(required = False, label = u"Screenshot #1")
    new_shot_2 = AppEngineImageField(required = False, label = u"Screenshot #2")
    new_shot_3 = AppEngineImageField(required = False, label = u"Screenshot #3")
    new_shot_4 = AppEngineImageField(required = False, label = u"Screenshot #4")
    new_shot_5 = AppEngineImageField(required = False, label = u"Screenshot #5")
    remove_list = forms.CharField(required = False, widget = forms.widgets.HiddenInput)

    def clean_remove_list(self):
        remove_list = self.cleaned_data["remove_list"]
        return [family.strip() for family in remove_list.split('|')]
