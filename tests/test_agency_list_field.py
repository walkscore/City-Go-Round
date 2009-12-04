import os
import logging
import unittest
from datetime import datetime

from bootstrap import bootstrap_django
bootstrap_django()

from django import forms

from google.appengine.ext import db
from citygoround.models import Agency
from citygoround.formfields import AgencyListField

class TestAgencyListField(unittest.TestCase):
    def setUp(self):
        self.field = AgencyListField(required = False)
        self.agency_1 = Agency(name="Test 1", city="San Francisco", state="CA", country="US", date_opened = datetime.fromtimestamp(0))
        self.agency_1.put()
        self.agency_2 = Agency(name="Test 2", city="San Francisco", state="CA", country="US", date_opened = datetime.fromtimestamp(0))
        self.agency_2.put()
        self.agency_3 = Agency(name="Test 3", city="San Francisco", state="CA", country="US", date_opened = datetime.fromtimestamp(0))
        self.agency_3.put()
        
    def tearDown(self):
        self.agency_1.delete()
        self.agency_2.delete()
        self.agency_3.delete()
                
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
        keys = self.try_validate('')
        self.assertEqual(keys, [])
        
    def test_invalid_key(self):
        self.try_invalidate('BOGUS')
        
    def test_invalid_keys(self):
        self.try_invalidate('EXCELLENT|BOGUS')
    
    def test_valid_key(self):
        keys = self.try_validate(str(self.agency_1.key()))
        self.assertEqual(len(keys), 1)
        self.assertEqual(keys[0], self.agency_1.key())

    def test_valid_keys(self):
        keys = self.try_validate("%s| %s" % (str(self.agency_1.key()), str(self.agency_3.key())))
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0], self.agency_1.key())
        self.assertEqual(keys[1], self.agency_3.key())

    def test_mixed_valid_invalid_keys(self):
        self.try_invalidate("%s | EXCELLENT | %s" % (str(self.agency_1.key()), str(self.agency_3.key())))
    

        
    