// immediately load maps API
google.load("maps", "2.167");

// TODO jesse: global variables are bad for your health. 
// Especially in the world of jQuery, it should always 
// be possible to have them local to _some_ scope...
data_manager = null;


function updateUI()
{			
	// TODO DAVEPECK HACK HACK
	if ( $("#global").is(":checked") )
	{
		$("#entire-us").attr("disabled", true);
		$("#choose-locations").attr("disabled", true);			 
	}
	else 
	{
		$("#entire-us").attr("disabled", false);
		$("#choose-locations").attr("disabled", false);
	}
	
	//show the location picker?
	if ( !$("#global").is(":checked") && $("#choose-locations").is(":checked") )
	{
		$("#location-list").show();
	}                      
	else                   
	{                      
		$("#location-list").hide();	
	}
}

$(document).ready(function() 
{
	data_manager = new DataManager();	
	$("#locations-form").submit(function() { data_manager.sendDataString(); });
	$("#add-query-button").click(function () { data_manager.addQuery(); });
	$("#global").click(updateUI);
	$("#entire-us").click(updateUI);
	$("#choose-locations").click(updateUI);	
	$("#query").keypress(function(event) 
	{ 
    	if (event.which==13)
    	{
    		data_manager.addQuery();
    		return false;
    	};
    });
});

//we keep a list of these, created when a user clicks "Add"
//on geoQuery return, we fill in the returned data into the existing object
//we also check to see if new objects have been added (serves as a queue)

//when a geocode doesn't get a country, we mark its entry as cancelled
//when a user resubmits that entry we overwrite the existing data and uncancel it

//when a user deletes an entry, we keep it in the list, but mark its entry as cancelled and delete the UI panel
function GeoQueryData(key, query) 
{
	this.key = key;
	this.query = query;
	this.geocoded = false;
	this.cancelled = false;
	this.city = null;
	this.country = null;
	this.geoLatLng = null;

	this.updateQuery = function(query)
	{
		this.query = query;
		this.geocoded = false;			
		//reset data:
		this.city = null;
		this.country = null;
		this.geoLatLng = null;
	}
	
	this.hasValidData = function()
	{
		return this.geoLatLng != null;
	}
	
	this.setData = function(city, administrativeArea, country, latlng)
	{			
		this.geocoded = true;

		//if succeeded
		if ( country && latlng )
		{
		    this.administrativeArea = administrativeArea;
			this.country = country;
			this.geoLatLng = latlng;
			if (city)					
			{
				this.city = city;			
			}
			this.cancelled = false;
			return true;
		}
		//geocode failed
		this.cancelled = true;
		return false;	
	}
	
	this.cancel = function(){ this.cancelled = true; }
	this.restoreEntry = function(){ this.cancelled = false; }
	this.isGeocoded = function(){ return this.geocoded }
	this.isCancelled = function(){ return this.cancelled }
	this.getKey = function(){ return this.key }
	this.getQuery = function(){ return this.query }
	this.getCity = function(){ return this.city }
	this.getCountry = function(){ return this.country }
	this.getLat = function(){ return this.geoLatLng.lat() }
	this.getLng = function(){ return this.geoLatLng.lng() }
	
	this.getDataString = function()
	{ 
		if ( this.city == null )
			return this.country;
		else 
			return this.geoLatLng.lat() + ", " + this.geoLatLng.lng() + ", " + this.city + ", " + this.administrativeArea + ", " + this.country;
	}
}

//manages the array of GeoQueryData
function QueryDataList()
{
	this.list = [];
	
	this.length = function() { return this.list.length }
	
	this.getByKey = function(key) 
	{ 
		for (var i = 0; i<this.list.length; i++)
		{
			if (this.list[i].key == key)
			{
				return this.list[i];
			}
		}
		return null;
	}
	
	this.addOrUpdateQuery = function(key, query)
	{
		var item = this.getByKey(key);
		if (item)
		{
			item.updateQuery(query);
			return 0;
		}
		else
		{
			this.list.push( new GeoQueryData(key, query) );
			return 1;
		}
	}
	
	this.getNextQuery = function()
	{
		for (var i = 0; i<this.list.length; i++)
		{
			if ( !this.list[i].isGeocoded() && !this.list[i].isCancelled() )
			{
				return this.list[i];
			}
		}		
		return null;		
	}
	
	this.cancelQuery = function(key)
	{
		var item = this.getByKey(key);
		if (item)
		{
			item.cancel();
		}
	}
	
	this.getDataString = function()
	{
		var str = '';
		for (var i = 0; i<this.list.length; i++)
		{
			if ( !this.list[i].isCancelled() && this.list[i].hasValidData() ) 
			{
				if (i>0)
				{
					str += " | ";
				}
				str += this.list[i].getDataString();
			}
		}		
		return str;
	}
}

//the main control class, this one runs the show
function DataManager() 
{
	this.geocoder = new Geocoder();
	this.queryDataList = new QueryDataList();
	this.numLocations = 0;
	this.activeQueryKey = -1;

	this.addQuery = function(key)
	{
		var query = $("#query").val();
		this.addDirectQuery(query);
		$("#query").focus().val("");
		this.geocodeQueuedQueries();
	}
	
	this.addDirectQuery = function(query)
	{
		if (this.queryDataList.addOrUpdateQuery(this.numLocations, query)) 
		{ 
		    //will always add, we don't allow editing old ones
			this.addLocation();
			this.numLocations++;
		}
    }
	
	this.addLocation = function()
	{
		var htmlStr = '<div id="location' + this.numLocations + '">';
		htmlStr += '<p id="name' + this.numLocations + '"></p>';
		htmlStr += '<a id="removelink' + this.numLocations + '" onclick="data_manager.removeQuery(' + this.numLocations + ')">remove</a>';
		htmlStr += '</div>';
		$("#locations").append(htmlStr);
	}
	
	this.removeQuery = function(key)
	{
		this.queryDataList.cancelQuery(key);
		$("#location"+key).hide("blind", { direction: "vertical" }, 1200);
	}
	
	this.geocodeQueuedQueries = function() 
	{
		if ( this.geocoder.isGeocoding() ) 
		{
			return;
		}
		//else, see if we have more to geocode:
		var nextQueryItem = this.queryDataList.getNextQuery();
		if ( nextQueryItem ) 
		{	
			this.activeQueryKey = nextQueryItem.getKey();		
			this.geocoder.geocode( nextQueryItem.getQuery(), bindCallback(this, this.handleGeocodeResponse) );
		}
	}

	this.handleGeocodeResponse = function(geodata)
	{
		this.geocoder.confirmSuccess();
		
		var currentQueryDataItem = this.queryDataList.getByKey(this.activeQueryKey);
		if (currentQueryDataItem ) 
		{
			currentQueryDataItem.setData(geodata.getCity(), geodata.getAdminArea(), geodata.getCountryCode(), geodata.getLatLng());
			if (currentQueryDataItem.hasValidData()) 
			{
				var countryName = fullCountryName(geodata.getCountryCode());
				var label = (geodata.hasCity()) ? "City" : "Country";
				var name = (geodata.hasCity()) ? geodata.getShorthand() : geodata.getCountryName();
				var entryText = name + " <span>(" + label + ")</span>"
				$( "#name" + this.activeQueryKey ).html(entryText);
				$( "#name" + this.activeQueryKey ).addClass("goodresult");
				$( "#removelink" + this.activeQueryKey ).show();
			}
			else 
			{
				$( "#name" + this.activeQueryKey ).html(currentQueryDataItem.getQuery() + " was not recognized.  Please try again.");
				var thisObj = this;
				var thisObjActiveQueryKey = this.activeQueryKey;
				setTimeout(function(){ thisObj.removeQuery(thisObjActiveQueryKey) }, 1000);
			}
		}
		else
		{
			alert("couldn't find item to set data on");
		}
			
		this.geocodeQueuedQueries();
	}
	
	this.getDataString = function()
	{
		var data = this.queryDataList.getDataString();
		var append = ( $("#entire-us").eq(0).is(":checked") ) ? (( data.length > 0 ) ? " | US" : "US") : "";
		alert( data + append);
	}
	
	this.sendDataString = function()
	{
		if ( !$("#global").eq(0).is(":checked") && $("#choose-locations").eq(0).is(":checked") )
		{
		    var data_string = this.getDataString();
			$("#id_location_list").val( data_string );
		}
		return true;
	}
}

function fullCountryName(code) 
{
	var name = countryLookups[code];
	if (name && name != "undefined")
	{
		return name;
	}
	return code;
}
var countryLookups = {"AX":"Aland Islands","AL":"Albania","DZ":"Algeria","AS":"American Samoa","AD":"Andorra","AO":"Angola","AI":"Anguilla","AQ":"Antarctica","AG":"Antigua and Barbuda","AR":"Argentina","AM":"Armenia","AW":"Aruba","AC":"Ascension Island","AU":"Australia","AT":"Austria","AZ":"Azerbaijan","BS":"Bahamas","BH":"Bahrain","BB":"Barbados","BD":"Bangladesh","BY":"Belarus","BE":"Belgium","BZ":"Belize","BJ":"Benin","BM":"Bermuda","BT":"Bhutan","BW":"Botswana","BO":"Bolivia","BA":"Bosnia and Herzegovina","BV":"Bouvet Island","BR":"Brazil","IO":"British Indian Ocean Territory","BN":"Brunei Darussalam","BG":"Bulgaria","BF":"Burkina Faso","BI":"Burundi","KH":"Cambodia","CM":"Cameroon","CA":"Canada","CV":"Cape Verde","KY":"Cayman Islands","CF":"Central African Republic","TD":"Chad","CL":"Chile","CN":"China","CX":"Christmas Island","CC":"Cocos (Keeling) Islands","CO":"Colombia","KM":"Comoros","CG":"Congo","CD":"Congo, Democratic Republic","CK":"Cook Islands","CR":"Costa Rica","CI":"Cote D'Ivoire (Ivory Coast)","HR":"Croatia (Hrvatska)","CU":"Cuba","CY":"Cyprus","CZ":"Czech Republic","CS":"Czechoslovakia (former)","DK":"Denmark","DJ":"Djibouti","DM":"Dominica","DO":"Dominican Republic","TP":"East Timor","EC":"Ecuador","EG":"Egypt","SV":"El Salvador","GQ":"Equatorial Guinea","ER":"Eritrea","EE":"Estonia","ET":"Ethiopia","FK":"Falkland Islands (Malvinas)","FO":"Faroe Islands","FJ":"Fiji","FI":"Finland","FR":"France","FX":"France, Metropolitan","GF":"French Guiana","PF":"French Polynesia","TF":"French Southern Territories","MK":"F.Y.R.O.M. (Macedonia)","GA":"Gabon","GM":"Gambia","GE":"Georgia","DE":"Germany","GH":"Ghana","GI":"Gibraltar","GB":"Great Britain (UK)","GR":"Greece","GL":"Greenland","GD":"Grenada","GP":"Guadeloupe","GU":"Guam","GT":"Guatemala","GN":"Guinea","GW":"Guinea-Bissau","GY":"Guyana","HT":"Haiti","HM":"Heard and McDonald Islands","HN":"Honduras","HK":"Hong Kong","HU":"Hungary","IS":"Iceland","IN":"India","ID":"Indonesia","IR":"Iran","IQ":"Iraq","IE":"Ireland","IL":"Israel","IM":"Isle of Man","IT":"Italy","JE":"Jersey","JM":"Jamaica","JP":"Japan","JO":"Jordan","KZ":"Kazakhstan","KE":"Kenya","KI":"Kiribati","KP":"Korea (North)","KR":"Korea (South)","KW":"Kuwait","KG":"Kyrgyzstan","LA":"Laos","LV":"Latvia","LB":"Lebanon","LI":"Liechtenstein","LR":"Liberia","LY":"Libya","LS":"Lesotho","LT":"Lithuania","LU":"Luxembourg","MO":"Macau","MG":"Madagascar","MW":"Malawi","MY":"Malaysia","MV":"Maldives","ML":"Mali","MT":"Malta","MH":"Marshall Islands","MQ":"Martinique","MR":"Mauritania","MU":"Mauritius","YT":"Mayotte","MX":"Mexico","FM":"Micronesia","MC":"Monaco","MD":"Moldova","MA":"Morocco","MN":"Mongolia","MS":"Montserrat","MZ":"Mozambique","MM":"Myanmar","NA":"Namibia","NR":"Nauru","NP":"Nepal","NL":"Netherlands","AN":"Netherlands Antilles","NT":"Neutral Zone","NC":"New Caledonia","NZ":"New Zealand (Aotearoa)","NI":"Nicaragua","NE":"Niger","NG":"Nigeria","NU":"Niue","NF":"Norfolk Island","MP":"Northern Mariana Islands","NO":"Norway","OM":"Oman","PK":"Pakistan","PW":"Palau","PS":"Palestinian Territory, Occupied","PA":"Panama","PG":"Papua New Guinea","PY":"Paraguay","PE":"Peru","PH":"Philippines","PN":"Pitcairn","PL":"Poland","PT":"Portugal","PR":"Puerto Rico","QA":"Qatar","RE":"Reunion","RO":"Romania","RU":"Russian Federation","RW":"Rwanda","GS":"S. Georgia and S. Sandwich Isls.","KN":"Saint Kitts and Nevis","LC":"Saint Lucia","VC":"Saint Vincent and the Grenadines","WS":"Samoa","SM":"San Marino","ST":"Sao Tome and Principe","SA":"Saudi Arabia","SN":"Senegal","YU":"Serbia and Montenegro","SC":"Seychelles","SL":"Sierra Leone","SG":"Singapore","SI":"Slovenia","SK":"Slovak Republic","SB":"Solomon Islands","SO":"Somalia","ZA":"South Africa","ES":"Spain","LK":"Sri Lanka","SH":"St. Helena","PM":"St. Pierre and Miquelon","SD":"Sudan","SR":"Suriname","SJ":"Svalbard and Jan Mayen Islands","SZ":"Swaziland","SE":"Sweden","CH":"Switzerland","SY":"Syria","TW":"Taiwan","TJ":"Tajikistan","TZ":"Tanzania","TH":"Thailand","TG":"Togo","TK":"Tokelau","TO":"Tonga","TT":"Trinidad and Tobago","TN":"Tunisia","TR":"Turkey","TM":"Turkmenistan","TC":"Turks and Caicos Islands","TV":"Tuvalu","UG":"Uganda","UA":"Ukraine","AE":"United Arab Emirates","UK":"United Kingdom","US":"United States","UM":"US Minor Outlying Islands","UY":"Uruguay","SU":"USSR (former)","UZ":"Uzbekistan","VU":"Vanuatu","VA":"Vatican City State","VE":"Venezuela","VN":"Viet Nam","VG":"British Virgin Islands","VI":"Virgin Islands (U.S.)","WF":"Wallis and Futuna Islands","EH":"Western Sahara","YE":"Yemen","ZM":"Zambia","ZR":"Zaire","ZW":"Zimbabwe"};


function dbug(str)
{
	$("#dbug").append(str + "<br />");
}

function dbugThese()
{
	dbug(Array.prototype.join.call(arguments, " :: "));
}

function reconstitute_country_from_code(country_code)
{
    var trimmed = $.trim(country_code);
    if (trimmed == "US")
    {
        $("#entire-us").click();
    }
    else
    {
        data_manager.addDirectQuery(countryLookups[country_code]);
    }
}

function reconstitute_city_from_lat_lon(lat, lon)
{
    data_manager.addDirectQuery(lat + "," + lon);
}

function reconstitute_city_from_details(lat, lon, city, administrative_area, country_code)
{
    data_manager.addDirectQuery(city + ", " + administrative_area + ", " + country_code);
}

function reconstitute_location_from_text(text)
{
    parts = text.split(',')
    if ($(parts).length == 1)
    {
        reconstitute_country_from_code(parts[0]);
    }
    else if ($(parts).length == 2)
    {
        reconstitute_city_from_lat_lon(parts[0], parts[1]);
    }
    else if ($(parts).length == 5)
    {
        reconstitute_city_from_details(parts[0], parts[1], parts[2], parts[3], parts[4]);
    }
    else
    {
        alert("Bad location text encountered; could not reconstitute: " + text);
    }
}

function reconstitute_locations(text)
{
    var clean_text = $.trim(text)
    if (clean_text.length > 0)
    {
        if (clean_text != "US")
        {
            $("#choose-locations").click();
        }
        locations = text.split('|');
        $.each(locations, function(i, location)
        {
            reconstitute_location_from_text(location);        
        });
        data_manager.geocodeQueuedQueries();	
    }
}