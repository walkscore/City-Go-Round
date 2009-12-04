import unittest
import logging
from copy import copy
from google.appengine.ext import db
from citygoround.models import Agency, TransitApp
from citygoround.utils.slug import slugify
from citygoround.utils.places import CityInfo, CitiesAndCountries, CountryInfo
from datetime import datetime

class TestAppAndAgency(unittest.TestCase):
    def setUp(self):
        self.public_agency_1 = Agency(name="Public 1", city="San Francisco", state="CA", country="US", location = db.GeoPt(37.7749295, -122.4194155), date_opened = datetime.fromtimestamp(0))
        self.public_agency_1.put()

        self.public_agency_2 = Agency(name="Public 2", city="Seattle", state="WA", country="US", location = db.GeoPt(47.6062095, -122.3320708), date_opened = datetime.fromtimestamp(0))
        self.public_agency_2.put()

        self.public_agency_3 = Agency(name="Public 3", city="Kokomo", state="IN", country="US", location = db.GeoPt(40.486427, -86.1336033), date_opened = datetime.fromtimestamp(0))
        self.public_agency_3.put()
        
        self.private_agency_1 = Agency(name="Private 1", city="Washington", state="DC", country="US", location = db.GeoPt(38.8951118, -77.0363658))
        self.private_agency_1.put()

        self.private_agency_2 = Agency(name="Private 2", city="Philadelphia", state="PA", country="US", location = db.GeoPt(39.952335, -75.163789))
        self.private_agency_2.put()

        self.private_agency_3 = Agency(name="Private 3", city="Mars", state="PA", country="US", location = db.GeoPt(40.6958996, -80.0117254))
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
        
        self.philadelphia = CityInfo(name="Philadelpha", administrative_area="PA", country_code="US", latitude=39.952335, longitude=-75.163789)
        self.narberth = CityInfo(name="Narberth", administrative_area="PA", country_code="US", latitude=40.0084456, longitude=-75.26046)
        self.berlin = CityInfo(name="Berlin", administrative_area="Berlin", country_code="DE", latitude=52.5234051, longitude=13.4113999)
        self.grants_pass = CityInfo(name="Grants Pass", administrative_area="OR", country_code="US", latitude=42.4390069, longitude=-123.3283925)
        self.portland = CityInfo(name="Portland", administrative_area="OR", country_code="US", latitude=45.5234515, longitude=-122.6762071)
        
        self.app_for_philadelphia = TransitApp(title = "app_for_philadelphia")
        self.app_for_philadelphia.put()
        self.app_for_philadelphia.add_explicitly_supported_city_info_immediate(self.philadelphia)        
        
        self.app_for_narberth = TransitApp(title = "app_for_narberth")
        self.app_for_narberth.put()
        self.app_for_narberth.add_explicitly_supported_city_info_immediate(self.narberth)
        
        self.app_for_entire_world = TransitApp(title = "app_for_entire_world", explicitly_supports_the_entire_world = True)
        self.app_for_entire_world.put()
        
        self.app_for_us = TransitApp(title = "app_for_us")
        self.app_for_us.add_explicitly_supported_country("US")
        self.app_for_us.put()
        
        self.app_for_de = TransitApp(title = "app_for_de")
        self.app_for_de.add_explicitly_supported_country("DE")
        self.app_for_de.put()
        
        self.app_for_portland = TransitApp(title = "app_for_portland")
        self.app_for_portland.put()
        self.app_for_portland.add_explicitly_supported_city_info_immediate(self.portland)
                
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
        
        self.app_for_philadelphia.delete()
        self.app_for_narberth.delete()
        self.app_for_entire_world.delete()
        self.app_for_us.delete()
        self.app_for_de.delete()
        self.app_for_portland.delete()
                
    def assertListsContainSameItems(self, list1, list2):
        self.assertTrue(len(list1) == len(list2), "FAIL: list lengths do not match. (GOT: %r for first list.)" % list1)
        list1_copy = copy(list1)
        list2_copy = copy(list2)
        list1_copy.sort()
        list2_copy.sort()
        self.assertTrue(list1_copy == list2_copy, "FAIL: lists did not match. (GOT: %r for first list.)" % list1)
        
        
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
        
        
    #--------------------------------------------------------------------------------
    # Test Search!
    #--------------------------------------------------------------------------------

    def test_search_1(self):
        apps = TransitApp.fetch_for_location_and_country_code(self.philadelphia.latitude, self.philadelphia.longitude, self.philadelphia.country_code)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_p2_p3", "app_pub_pub2_pub3_p1_p2", "app_for_philadelphia", "app_for_entire_world", "app_for_us"])

    def test_search_2(self):
        apps = TransitApp.fetch_for_location_and_country_code(self.narberth.latitude, self.narberth.longitude, self.narberth.country_code)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_for_narberth", "app_for_entire_world", "app_for_us"])

    def test_search_3(self):
        apps = TransitApp.fetch_for_location_and_country_code(self.narberth.latitude, self.narberth.longitude, self.narberth.country_code, bbox_side_in_miles = 50.0)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_for_narberth", "app_p2_p3", "app_pub_pub2_pub3_p1_p2", "app_for_philadelphia", "app_for_entire_world", "app_for_us"])

    def test_search_4(self):
        apps = TransitApp.fetch_for_location_and_country_code(self.berlin.latitude, self.berlin.longitude, self.berlin.country_code)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_for_de", "app_for_entire_world"])

    def test_search_5(self):
        apps = TransitApp.fetch_for_location_and_country_code(self.grants_pass.latitude, self.grants_pass.longitude, self.grants_pass.country_code, bbox_side_in_miles = 1000.0)
        app_titles = [app.title for app in apps]
        self.assertListsContainSameItems(app_titles, ["app_pub", "app_pub_p1_p3", "app_pub_pub2_pub3_p1_p2", "app_for_portland", "app_for_us", "app_for_entire_world"])
