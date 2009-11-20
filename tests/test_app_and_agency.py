import unittest
import logging
from copy import copy
from google.appengine.ext import db
from opentransit.models import Agency, TransitApp
from opentransit.utils.slug import slugify
from datetime import datetime

class TestAppAndAgency(unittest.TestCase):
    def setUp(self):
        self.public_agency_1 = Agency(name="Public 1", city="San Francisco", state="CA", country="US", date_opened = datetime.fromtimestamp(0))
        self.public_agency_1.put()

        self.public_agency_2 = Agency(name="Public 2", city="Seattle", state="WA", country="US", date_opened = datetime.fromtimestamp(0))
        self.public_agency_2.put()

        self.public_agency_3 = Agency(name="Public 3", city="Kokomo", state="IN", country="US", date_opened = datetime.fromtimestamp(0))
        self.public_agency_3.put()
        
        self.private_agency_1 = Agency(name="Private 1", city="Washington", state="DC", country="US")
        self.private_agency_1.put()

        self.private_agency_2 = Agency(name="Private 2", city="Philadelphia", state="PA", country="US")
        self.private_agency_2.put()

        self.private_agency_3 = Agency(name="Private 3", city="Mars", state="PA", country="US")
        self.private_agency_3.put()
        
        self.app_pub = TransitApp(title = "app_pub", supports_all_public_agencies = True)
        self.app_pub.put()
        
        self.app_p1 = TransitApp(title = "app_p1")
        self.app_p1.add_explicitly_supported_agency(self.private_agency_1)
        self.app_p1.put()
        
        self.app_p2_p3 = TransitApp(title = "app_p2_p3")
        self.app_p2_p3.add_explicitly_supported_agencies([self.private_agency_2, self.private_agency_3])
        self.app_p2_p3.put()
        
        self.app_pub_p1_p3 = TransitApp(title = "app_pub_p1_p3", supports_all_public_agencies = True)
        self.app_pub_p1_p3.add_explicitly_supported_agencies([self.private_agency_1, self.private_agency_3])
        self.app_pub_p1_p3.put()
        
        self.app_pub_pub2_pub3_p1_p2 = TransitApp(title = "app_pub_pub2_pub3_p1_p2", supports_all_public_agencies = True)
        self.app_pub_pub2_pub3_p1_p2.add_explicitly_supported_agencies([self.public_agency_2, self.public_agency_3, self.private_agency_1, self.private_agency_2])
        self.app_pub_pub2_pub3_p1_p2.put()
        
    def tearDown(self):
        self.public_agency_1.delete()
        self.public_agency_2.delete()
        self.public_agency_3.delete()
        self.private_agency_1.delete()
        self.private_agency_2.delete()
        self.private_agency_3.delete()
        
        self.app_pub.delete()
        self.app_p1.delete()
        self.app_p2_p3.delete()
        self.app_pub_p1_p3.delete()
        self.app_pub_pub2_pub3_p1_p2.delete()
                
    def assertListsContainSameItems(self, list1, list2):
        self.assertTrue(len(list1) == len(list2), "FAIL: list lengths do not match.")
        list1_copy = copy(list1)
        list2_copy = copy(list2)
        list1_copy.sort()
        list2_copy.sort()
        self.assertTrue(list1_copy == list2_copy, "FAIL: lists did not match.")
        
        
    #--------------------------------------------------------------------------
    # Given an app, get a list of agencies
    #--------------------------------------------------------------------------
    
    def test_find_list_of_agencies_given_app_1(self):
        agencies = Agency.fetch_for_transit_app(self.app_pub)
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Public 1", "Public 2", "Public 3"])
        
    def test_find_list_of_agencies_given_app_2(self):        
        agencies = Agency.fetch_for_transit_app(self.app_p1)
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Private 1"])

    def test_find_list_of_agencies_given_app_3(self):        
        agencies = Agency.fetch_for_transit_app(self.app_p2_p3)
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Private 2", "Private 3"])
    
    def test_find_list_of_agencies_given_app_4(self):
        agencies = Agency.fetch_for_transit_app(self.app_pub_p1_p3)
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Public 1", "Public 2", "Public 3", "Private 1", "Private 3"])

    def test_find_list_of_agencies_given_app_5(self):
        agencies = Agency.fetch_for_transit_app(self.app_pub_pub2_pub3_p1_p2)
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Public 1", "Public 2", "Public 3", "Private 1", "Private 2"])

    def test_find_list_of_agencies_given_app_with_uniquify_off(self):
        agencies = Agency.fetch_for_transit_app(self.app_pub_pub2_pub3_p1_p2, uniquify = False)
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Public 1", "Public 2", "Public 3", "Public 2", "Public 3", "Private 1", "Private 2"])


    #-----------------------------------------------------------------------------
    # Given a list of apps, get a list of agencies supported by at least one app
    #-----------------------------------------------------------------------------

    def test_find_list_of_agencies_given_apps_1(self):
        agencies = Agency.fetch_for_transit_apps([self.app_p1, self.app_p2_p3])
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Private 1", "Private 2", "Private 3"])
    
    def test_find_list_of_agencies_given_apps_2(self):
        agencies = Agency.fetch_for_transit_apps([self.app_pub_pub2_pub3_p1_p2, self.app_p2_p3])
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Public 1", "Public 2", "Public 3", "Private 1", "Private 2", "Private 3"])
        
    def test_find_list_of_agencies_given_apps_with_uniquify_off(self):
        agencies = Agency.fetch_for_transit_apps([self.app_pub_pub2_pub3_p1_p2, self.app_p2_p3], uniquify = False)
        agency_names = [agency.name for agency in agencies]
        self.assertListsContainSameItems(agency_names, ["Public 1", "Public 2", "Public 3", "Public 2", "Public 3", "Private 1", "Private 2", "Private 2", "Private 3"])

        
    #-----------------------------------------------------------------------------
    # Given a agency, get a list of apps
    #-----------------------------------------------------------------------------
        
    def test_find_list_of_apps_given_agency_1(self):
        apps = TransitApp.fetch_for_agency(self.public_agency_1)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_pub", "app_pub_p1_p3", "app_pub_pub2_pub3_p1_p2"])

    def test_find_list_of_apps_given_agency_2(self):
        apps = TransitApp.fetch_for_agency(self.public_agency_2)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_pub", "app_pub_p1_p3", "app_pub_pub2_pub3_p1_p2"])

    def test_find_list_of_apps_given_agency_3(self):
        apps = TransitApp.fetch_for_agency(self.public_agency_3)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_pub", "app_pub_p1_p3", "app_pub_pub2_pub3_p1_p2"])
        
    def test_find_list_of_apps_given_agency_4(self):
        apps = TransitApp.fetch_for_agency(self.private_agency_1)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_p1", "app_pub_p1_p3", "app_pub_pub2_pub3_p1_p2"])

    def test_find_list_of_apps_given_agency_5(self):
        apps = TransitApp.fetch_for_agency(self.private_agency_2)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_p2_p3", "app_pub_pub2_pub3_p1_p2"])

    def test_find_list_of_apps_given_agency_6(self):
        apps = TransitApp.fetch_for_agency(self.private_agency_3)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_p2_p3", "app_pub_p1_p3"])

    def test_find_list_of_apps_given_agency_with_uniquify_off(self):
        apps = TransitApp.fetch_for_agency(self.public_agency_2, uniquify = False)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_pub", "app_pub_p1_p3", "app_pub_pub2_pub3_p1_p2", "app_pub_pub2_pub3_p1_p2"])
        
        
    #--------------------------------------------------------------------------------
    # Given a list of agencies, get a list of apps that support at least one agency
    #--------------------------------------------------------------------------------
        
    def test_find_list_of_apps_given_agencies_1(self):
        apps = TransitApp.fetch_for_agencies([self.public_agency_1, self.private_agency_3])
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_pub", "app_p2_p3", "app_pub_p1_p3", "app_pub_pub2_pub3_p1_p2"])

    def test_find_list_of_apps_given_agencies_with_uniquify_off(self):
        apps = TransitApp.fetch_for_agencies([self.public_agency_1, self.private_agency_3], uniquify = False)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_pub", "app_p2_p3", "app_pub_p1_p3", "app_pub_p1_p3", "app_pub_pub2_pub3_p1_p2"])
        
