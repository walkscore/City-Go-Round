import os
import logging
import unittest

from bootstrap import bootstrap_django
bootstrap_django()

from django import forms

from opentransit.formfields import LocationListField


class TestLocationListField(unittest.TestCase):
    def setUp(self):
        self.field = LocationListField(required = False)
        
    def tearDown(self):
        pass
                
    def try_validate(self, value):
        try:
            result = self.field.clean(value)
        except forms.ValidationError, error:
            self.fail("Field did not validate with %r (%s)" % (value, str(error)))
        return result
            
    def try_invalidate(self, value):
        try:
            result = self.field.clean(value)
        except forms.ValidationError, error:
            return
        self.fail("Field validated with %r" % value)        
        
    def test_none(self):
        self.try_invalidate(None)
    
    def test_empty(self):
        info = self.try_validate('')
        self.assertEqual(len(info.cities), 0)
        self.assertEqual(len(info.countries), 0)
        
    def test_single_country(self):
        info = self.try_validate('US')
        self.assertEqual(len(info.cities), 0)
        self.assertEqual(len(info.countries), 1)
        self.assertEqual(info.countries[0].country_code, 'US')
    
    def test_multiple_countries(self):
        info = self.try_validate('US|UK|CA')
        self.assertEqual(len(info.cities), 0)
        self.assertEqual(len(info.countries), 3)
        self.assertEqual(info.countries[0].country_code, 'US')
        self.assertEqual(info.countries[1].country_code, 'UK')
        self.assertEqual(info.countries[2].country_code, 'CA')
        
    def test_invalid_country(self):
        self.try_invalidate('UKK')
        self.try_invalidate('U')
        
    def test_invalid_countries(self):
        self.try_invalidate('US|UK|X')
        self.try_invalidate('US||X')
        self.try_invalidate('US|NEATOBURRITO|UK')
        
    def test_single_city(self):
        info = self.try_validate('47.6062, -122.3320, Seattle, WA, US')
        self.assertEqual(len(info.cities), 1)
        self.assertEqual(len(info.countries), 0)
        city = info.cities[0]
        self.assertEqual(city.name, 'Seattle')
        self.assertEqual(city.latitude, float('47.6062'))
        self.assertEqual(city.longitude, float('-122.3320'))
        self.assertEqual(city.administrative_area, 'WA')
        self.assertEqual(city.country_code, 'US')
        
    def test_multiple_cities(self):
        info = self.try_validate('47.6062, -122.3320, Seattle, WA, US|47.6062, -122.3320, Seattle, WA, US| 47.6062, -122.3320, Seattle, WA, US')
        self.assertEqual(len(info.cities), 3)
        self.assertEqual(len(info.countries), 0)
        for city in info.cities:
            self.assertEqual(city.name, 'Seattle')
            self.assertEqual(city.latitude, float('47.6062'))
            self.assertEqual(city.longitude, float('-122.3320'))
            self.assertEqual(city.administrative_area, 'WA')
            self.assertEqual(city.country_code, 'US')
            
    def test_invalid_city(self):
        self.try_invalidate('47.6062, -122.GOOBER3320, Seattle, WA, US')    
        self.try_invalidate('47.6062,, Seattle, WA, US')    
        self.try_invalidate('47.6062, -122.3320, Seattle, W, US')    
        self.try_invalidate('47.6062, -122.3320, Seattle, WA, USZZZ')    
        self.try_invalidate('47.6062, -122.3320, Seattle, W, USZZZ')    
        
    def test_invalid_cities(self):
        self.try_invalidate('47.6062, -122.3320, Seattle, WA, US|47.6062,, Seattle, WA, US')    
        self.try_invalidate('47.6062, -122.3320, Seattle, WA, US|47.6062, -122.3320, Seattle, WA, US|47.6062,, Seattle, WA, US')    

    def test_city_and_country(self):
        info = self.try_validate('47.6062, -122.3320, Seattle, WA, US|GB')
        self.assertEqual(len(info.cities), 1)
        self.assertEqual(len(info.countries), 1)
        city = info.cities[0]
        self.assertEqual(city.name, 'Seattle')
        self.assertEqual(city.latitude, float('47.6062'))
        self.assertEqual(city.longitude, float('-122.3320'))
        self.assertEqual(city.administrative_area, 'WA')
        self.assertEqual(city.country_code, 'US')
        self.assertEqual(info.countries[0].country_code, 'GB')
        
    def test_cities_and_countries(self):
        info = self.try_validate('47.6062, -122.3320, Seattle, WA, US|GB|47.6062, -122.3320, Seattle, WA, US|CA|47.6062, -122.3320, Seattle, WA, US')
        self.assertEqual(len(info.cities), 3)
        self.assertEqual(len(info.countries), 2)
        
    