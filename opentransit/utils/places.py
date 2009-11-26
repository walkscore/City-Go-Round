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

COUNTRY_CODES = {"AX":"Aland Islands","AL":"Albania","DZ":"Algeria","AS":"American Samoa","AD":"Andorra","AO":"Angola","AI":"Anguilla","AQ":"Antarctica","AG":"Antigua and Barbuda","AR":"Argentina","AM":"Armenia","AW":"Aruba","AC":"Ascension Island","AU":"Australia","AT":"Austria","AZ":"Azerbaijan","BS":"Bahamas","BH":"Bahrain","BB":"Barbados","BD":"Bangladesh","BY":"Belarus","BE":"Belgium","BZ":"Belize","BJ":"Benin","BM":"Bermuda","BT":"Bhutan","BW":"Botswana","BO":"Bolivia","BA":"Bosnia and Herzegovina","BV":"Bouvet Island","BR":"Brazil","IO":"British Indian Ocean Territory","BN":"Brunei Darussalam","BG":"Bulgaria","BF":"Burkina Faso","BI":"Burundi","KH":"Cambodia","CM":"Cameroon","CA":"Canada","CV":"Cape Verde","KY":"Cayman Islands","CF":"Central African Republic","TD":"Chad","CL":"Chile","CN":"China","CX":"Christmas Island","CC":"Cocos (Keeling) Islands","CO":"Colombia","KM":"Comoros","CG":"Congo","CD":"Congo, Democratic Republic","CK":"Cook Islands","CR":"Costa Rica","CI":"Cote D'Ivoire (Ivory Coast)","HR":"Croatia (Hrvatska)","CU":"Cuba","CY":"Cyprus","CZ":"Czech Republic","CS":"Czechoslovakia (former)","DK":"Denmark","DJ":"Djibouti","DM":"Dominica","DO":"Dominican Republic","TP":"East Timor","EC":"Ecuador","EG":"Egypt","SV":"El Salvador","GQ":"Equatorial Guinea","ER":"Eritrea","EE":"Estonia","ET":"Ethiopia","FK":"Falkland Islands (Malvinas)","FO":"Faroe Islands","FJ":"Fiji","FI":"Finland","FR":"France","FX":"France, Metropolitan","GF":"French Guiana","PF":"French Polynesia","TF":"French Southern Territories","MK":"F.Y.R.O.M. (Macedonia)","GA":"Gabon","GM":"Gambia","GE":"Georgia","DE":"Germany","GH":"Ghana","GI":"Gibraltar","GB":"Great Britain (UK)","GR":"Greece","GL":"Greenland","GD":"Grenada","GP":"Guadeloupe","GU":"Guam","GT":"Guatemala","GN":"Guinea","GW":"Guinea-Bissau","GY":"Guyana","HT":"Haiti","HM":"Heard and McDonald Islands","HN":"Honduras","HK":"Hong Kong","HU":"Hungary","IS":"Iceland","IN":"India","ID":"Indonesia","IR":"Iran","IQ":"Iraq","IE":"Ireland","IL":"Israel","IM":"Isle of Man","IT":"Italy","JE":"Jersey","JM":"Jamaica","JP":"Japan","JO":"Jordan","KZ":"Kazakhstan","KE":"Kenya","KI":"Kiribati","KP":"Korea (North)","KR":"Korea (South)","KW":"Kuwait","KG":"Kyrgyzstan","LA":"Laos","LV":"Latvia","LB":"Lebanon","LI":"Liechtenstein","LR":"Liberia","LY":"Libya","LS":"Lesotho","LT":"Lithuania","LU":"Luxembourg","MO":"Macau","MG":"Madagascar","MW":"Malawi","MY":"Malaysia","MV":"Maldives","ML":"Mali","MT":"Malta","MH":"Marshall Islands","MQ":"Martinique","MR":"Mauritania","MU":"Mauritius","YT":"Mayotte","MX":"Mexico","FM":"Micronesia","MC":"Monaco","MD":"Moldova","MA":"Morocco","MN":"Mongolia","MS":"Montserrat","MZ":"Mozambique","MM":"Myanmar","NA":"Namibia","NR":"Nauru","NP":"Nepal","NL":"Netherlands","AN":"Netherlands Antilles","NT":"Neutral Zone","NC":"New Caledonia","NZ":"New Zealand (Aotearoa)","NI":"Nicaragua","NE":"Niger","NG":"Nigeria","NU":"Niue","NF":"Norfolk Island","MP":"Northern Mariana Islands","NO":"Norway","OM":"Oman","PK":"Pakistan","PW":"Palau","PS":"Palestinian Territory, Occupied","PA":"Panama","PG":"Papua New Guinea","PY":"Paraguay","PE":"Peru","PH":"Philippines","PN":"Pitcairn","PL":"Poland","PT":"Portugal","PR":"Puerto Rico","QA":"Qatar","RE":"Reunion","RO":"Romania","RU":"Russian Federation","RW":"Rwanda","GS":"S. Georgia and S. Sandwich Isls.","KN":"Saint Kitts and Nevis","LC":"Saint Lucia","VC":"Saint Vincent and the Grenadines","WS":"Samoa","SM":"San Marino","ST":"Sao Tome and Principe","SA":"Saudi Arabia","SN":"Senegal","YU":"Serbia and Montenegro","SC":"Seychelles","SL":"Sierra Leone","SG":"Singapore","SI":"Slovenia","SK":"Slovak Republic","SB":"Solomon Islands","SO":"Somalia","ZA":"South Africa","ES":"Spain","LK":"Sri Lanka","SH":"St. Helena","PM":"St. Pierre and Miquelon","SD":"Sudan","SR":"Suriname","SJ":"Svalbard and Jan Mayen Islands","SZ":"Swaziland","SE":"Sweden","CH":"Switzerland","SY":"Syria","TW":"Taiwan","TJ":"Tajikistan","TZ":"Tanzania","TH":"Thailand","TG":"Togo","TK":"Tokelau","TO":"Tonga","TT":"Trinidad and Tobago","TN":"Tunisia","TR":"Turkey","TM":"Turkmenistan","TC":"Turks and Caicos Islands","TV":"Tuvalu","UG":"Uganda","UA":"Ukraine","AE":"United Arab Emirates","UK":"United Kingdom","US":"United States","UM":"US Minor Outlying Islands","UY":"Uruguay","SU":"USSR (former)","UZ":"Uzbekistan","VU":"Vanuatu","VA":"Vatican City State","VE":"Venezuela","VN":"Viet Nam","VG":"British Virgin Islands","VI":"Virgin Islands (U.S.)","WF":"Wallis and Futuna Islands","EH":"Western Sahara","YE":"Yemen","ZM":"Zambia","ZR":"Zaire","ZW":"Zimbabwe"};

def country_name_from_country_code(country_code):
    return COUNTRY_CODES[country_code]