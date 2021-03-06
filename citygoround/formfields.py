from django import forms
from django.conf import settings
from google.appengine.api import images
from google.appengine.ext import db
from django.utils.translation import ugettext_lazy as _
from .utils.image import convert_image
from .utils.places import CityInfo, CountryInfo, CitiesAndCountries
from .nameddict import nameddict
# from bootstrap import BREAKPOINT

class AppEngineImageField(forms.FileField):
    # Django's built-in ImageField doesn't work on AppEngine because
    # it relies on unavailable PIL APIs. Here's my own version that works.

    image_error_messages = {
        'invalid_image': _(u"Upload a valid image. The file you uploaded was either not an image or was a corrupted image."),
        'too_large_image': _(u"Your image was too large. Please keep images under 1MB in size."),
        'too_large_converted_image': _(u"Your image was too large. Please try again with a smaller image."),
    }
    
    def __init__(self, target_output_encoding = images.PNG, *args, **kwargs):
        super(AppEngineImageField, self).__init__(*args, **kwargs)
        self._target_output_encoding = target_output_encoding
    
    def clean(self, data, initial = None):
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
            except (TypeError, KeyError, ValueError):
                bytes = None
        
        if bytes is None:
            raise forms.ValidationError(self.image_error_messages['invalid_image'])
        
        if len(bytes) > settings.MAX_IMAGE_SIZE:
            raise forms.ValidationError(self.image_error_messages['too_large_image'])
                        
        if len(bytes) > 0:
            converted = convert_image(bytes, output_encoding = self._target_output_encoding)
            if not converted:
                raise forms.ValidationError(self.image_error_messages['invalid_image'])
            # Fix bmander/issues#99 -- but note that, long term, we want to fix bmander/issues#100 as well
            if len(converted) > settings.MAX_IMAGE_SIZE:
                raise forms.ValidationError(self.image_error_messages['too_large_converted_image'])
        
        if hasattr(raw_file, 'seek') and callable(raw_file.seek):
            raw_file.seek(0)
            
        return raw_file

class LocationListField(forms.CharField):
    # Very special-purpose form designed to handle data from our 
    # "associate app with cities and countries" signup form.
    #
    # Format:
    # 
    #   Location_1|Location_2|Location_3
    #
    # Where each Location has the format:
    #
    #   lat.itude,long.itude,city name,state name,CC
    #
    # if it is for a specific city, or:
    #
    #   CC
    #
    # (a two-character country code) if it is for an entire country
    
    location_error_messages = {
        'no_locations': _(u"At least one location must be provided."),
        'invalid_country_code': _(u"Received an invalid country code."),
        'malformed_city_info': _(u"Malformed city information."),
        'invalid_location_list': _(u"Invalid location list. This should have been automatically generated by JavaScript, so you should never see this message."),
    }
    
    def _clean_country_code(self, country_code_x):
        country_code = country_code_x.strip()
        if len(country_code) != 2:
            raise forms.ValidationError(self.location_error_messages['invalid_country_code'])
        return CountryInfo(country_code = country_code)
        
    def _clean_city(self, latitude_x, longitude_x, city_name_x, administrative_area_x, country_code_x):
        try:
            latitude = float(latitude_x)
            longitude = float(longitude_x)
        except (TypeError, ValueError):
            raise forms.ValidationError(self.location_error_messages['malformed_city_info'])    
                    
        city_name = city_name_x.strip()
        if len(city_name) < 2:
            raise forms.ValidationError(self.location_error_messages['malformed_city_info'])
                    
        administrative_area = administrative_area_x.strip()
        if len(administrative_area) < 2:
            raise forms.ValidationError(self.location_error_messages['malformed_city_info'])
        
        country_code = country_code_x.strip()
        if len(country_code) != 2:
            raise forms.ValidationError(self.location_error_messages['malformed_city_info'])
            
        return CityInfo(latitude = latitude, longitude = longitude, name = city_name, administrative_area = administrative_area, country_code = country_code)
            
    def clean(self, value):
        super(LocationListField, self).clean(value)   
        
        if (value is None):
            raise forms.ValidationError(self.location_error_messages['no_locations'])
        
        if len(value.strip()) < 1:
            return CitiesAndCountries(cities = [], countries = [])
                   
        all_countries = []
        all_cities = []
               
        location_infos = value.strip().split('|')
        for location_info in location_infos:
            location_parts = location_info.split(',')
            if len(location_parts) == 1:
                all_countries.append(self._clean_country_code(*location_parts))
            elif len(location_parts) == 5:
                all_cities.append(self._clean_city(*location_parts))
            else:
                raise forms.ValidationError(self.location_error_messages['malformed_city_info'])
        
        return CitiesAndCountries(cities = all_cities, countries = all_countries)
                
class AgencyListField(forms.CharField):
    # Very special-purpose form designed to handle data from our 
    # "associate app with transit signup form.
    #
    # (CONSIDER davepeck: use of appengine datastore keys is potentially 
    # brittle, if we happen to be updating agencies when users are filling
    # out this form. Bah. Forget it for now.)
    #
    # Format:
    # 
    #   Agency_Key_1|Agency_Key_2|...    
    
    agency_error_messages = {
        'malformed_agency_list': _(u"Malformed agency list. This should have been automatically generated by JavaScript, so you should never see this message."),
        'invalid_agency_key': _(u"Invalid agency key."),        
    }
    
    def clean(self, value):
        super(AgencyListField, self).clean(value)         
        if (value is None):
            raise forms.ValidationError(self.agency_error_messages['malformed_agency_list'])
            
        if len(value.strip()) < 1:
            return []
            
        try:
            encoded_keys = value.strip().split('|')
            datastore_keys = [db.Key(encoded_key.strip()) for encoded_key in encoded_keys]
        except (AttributeError, TypeError, ValueError, db.Error):
            raise forms.ValidationError(self.agency_error_messages['invalid_agency_key'])
            
        return datastore_keys
        
