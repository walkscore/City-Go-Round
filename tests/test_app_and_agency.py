import unittest
import logging
from google.appengine.ext import db
from opentransit.models import Agency, TransitApp

class TestAppAndAgency(unittest.TestCase):
    def setUp(self):
        logging.info('In setUp()')
        
    def tearDown(self):
        logging.info('In tearDown()')

    def test_should_fail(self):
        logging.info('Running test_should_fail')
        self.assertTrue(False, "Good! It failed!")
        
    def test_should_succeed(self):
        logging.info('Running test_should_succeed')
        self.assertTrue(True, "Whoops! It failed!")
        