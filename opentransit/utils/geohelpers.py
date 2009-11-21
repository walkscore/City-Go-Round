import math
import logging
from geo import geotypes

class Constants(object):
    PI_OVER_180 = math.pi / 180.0
    EARTH_RADIUS_IN_METERS = 6378137.0
    ONE_LATITUDINAL_DEGREE_IN_METERS_AT_SEA_LEVEL = 110900.0
    METERS_PER_MILE = 1609.344

def width_of_latitudinal_degree_in_meters():
    return Constants.ONE_LATITUDINAL_DEGREE_IN_METERS_AT_SEA_LEVEL
    
def width_of_longitudinal_degree_in_meters_for_latitude(latitude):
    # assumes earth of constant radius; we could be more precise if we cared
    latitude_in_radians = math.radians(latitude)
    return math.cos(latitude_in_radians) * Constants.PI_OVER_180 * Constants.EARTH_RADIUS_IN_METERS

def latitudinal_degrees_from_meters(meters):
    return meters / Constants.ONE_LATITUDINAL_DEGREE_IN_METERS_AT_SEA_LEVEL
    
def longitudinal_degrees_from_meters_at_latitude(meters, latitude):
    one_longitudinal_degree_in_meters = width_of_longitudinal_degree_in_meters_for_latitude(latitude)
    return meters / one_longitudinal_degree_in_meters

def miles_to_meters(miles):
    return miles * Constants.METERS_PER_MILE
    
def meters_to_miles(meters):
    return meters / Constants.METERS_PER_MILE

def square_bounding_box_centered_at(latitude, longitude, side_in_miles):
    side_in_meters = miles_to_meters(side_in_miles)
    latitude_halfside_in_degrees = latitudinal_degrees_from_meters(side_in_meters) / 2.0
    longitude_halfside_in_degrees = longitudinal_degrees_from_meters_at_latitude(side_in_meters, latitude) / 2.0
    return geotypes.Box(
        north = latitude + latitude_halfside_in_degrees,
        east = longitude + longitude_halfside_in_degrees,
        south = latitude - latitude_halfside_in_degrees,
        west = longitude - longitude_halfside_in_degrees )

def are_latitude_and_longitude_valid(latitude, longitude):
    return (abs(latitude) <= 90.0) and (abs(longitude) <= 180.0)
