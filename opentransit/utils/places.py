from ..nameddict import nameddict
from .slug import slugify
from .misc import uniquify

CityInfoBase = nameddict("CityInfo", keys=["latitude", "longitude", "name", "administrative_area", "country_code"])

class CityInfo(CityInfoBase):
    def __init__(self, *args, **kwargs):
        super(CityInfo, self).__init__(*args, **kwargs)
    
    @property
    def name_slug(self):
        return slugify(self.name)
            
    @property
    def important_details(self):
        return "%s, %s, %s" % (self.name, self.administrative_area, self.country_code)

CountryInfo = nameddict("CountryInfo", keys=["country_code"])

CitiesAndCountriesBase = nameddict("CitiesAndCountries", keys=["cities", "countries"])
                
class CitiesAndCountries(CitiesAndCountriesBase):
    def __init__(self, *args, **kwargs):
        super(CitiesAndCountries, self).__init__(*args, **kwargs)
        
    @property
    def unique_cities(self):
        seen = set()
        for city in self.cities:
            if city.important_details not in seen:
                seen.add(city.important_details)
                yield city
        
    @property
    def unique_countries(self):
        seen = set()
        for country in self.countries:
            if country.country_code not in seen:
                seen.add(country.country_code)
                yield country
