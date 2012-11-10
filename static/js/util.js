// © Walk Score 2012

//*********** Utility functions ***********
		function getUrlParam( name, doEscapeCleaning, doAddressCleaning) {
			name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
			var regexS = "[\\?&]"+name+"=([^&#]*)";
			var regex = new RegExp( regexS );
			var results = regex.exec( window.location.href );
			if( results == null ) {
				return "";
			}
			else {
				var ret = results[1];
				if (doEscapeCleaning) ret = cleanEscapes(ret);
				if (doAddressCleaning) ret = cleanAddress(ret);
				return ret;
			}
		}

		function cleanEscapes(address) {
			address = unescape(address);
			address = replaceAll( address, "+", " " );
			return address;
		}

		function cleanAddress(address) {
			address = replaceAll( address, "&", " and " );
			//address = replaceAll( address, "#", " " );
			return address;
		}

		function replaceAll (strOrig, strTarget, strSubString) {
			var intIndexOfMatch = strOrig.indexOf( strTarget );
			while (intIndexOfMatch != -1) {
				strOrig = strOrig.replace( strTarget, strSubString )
				intIndexOfMatch = strOrig.indexOf( strTarget );
			}
			return strOrig;
		}

		function urlify(name, value, excludeNulls) {
			return (value == null && excludeNulls) ? "" : name + "=" + encodeURIComponent(value);
		}

		function sluggify(string) {
			string = replaceAll( string, " ", "-" );
			string = replaceAll( string, "'", "" );
			return string.toLowerCase();
		}

		// if str is not a string, returns ""
		function safeString(str, addLeadingSpace, addTrailingSpace){
			if (typeof str != "string")
				return "";
			if (addLeadingSpace) str = " " + str;
			if (addTrailingSpace) str = str + " ";
			return str;
		}

		function trimURL(url) {
			var i = url.indexOf("://");
			if (i != -1)
				return url.substr(i+3);
		}

		function forEach(array, fn, objThis) {
			objThis = objThis || this;
			var len = array.length;
			for (var n = 0; n < len; n++) {
				var r = fn.call(objThis, array[n], n);
				if (r !== undefined)
					return r;
			}
		}

		function paramIsSet(param) {
			return (typeof param != "undefined");
		}

		function defaultIfNotSet(param, defaultVal) {
			return (typeof param != "undefined") ? param : defaultVal;
		}

		function trackEvent(control, action, label, value) {
			//alertThese("Track Event", control, action, label, value);
			if(pageTracker)
				pageTracker._trackEvent(control, action, label, value);
		}

		function trackNavigation(url, component, action, label) {
			if (component && action)
				trackEvent(component, action, safeString(label) );
			if (url)
				document.location = url;
		}

		function trackNavigationNewWindow(url, component, action, label) {
			if (component && action)
				trackEvent(component, action, safeString(label) );
			if (url)
				window.open( url, "newwin" );
		}
		function isNumeric(str){
			var numericExpression = /^[0-9]+$/;
			if (str.match(numericExpression))
				return true;
			return false;
		}

		function leadsWithNumber(str){
			var numericExpression = /^[0-9]+$/;
			if (str.substr(0,1).match(numericExpression))
				return true;
			return false;
		}

		function getLeadingNumber(str){
			if (!leadsWithNumber(str))
				return false
			var r = str.match(/[\d\.]+/g);
			if (r && r[0])
				return Number(r[0]);
			return false;
		}


//*********** JS OOP ******************
	Function.prototype.inheritsFrom = function( parentClassOrObject ){
		if ( parentClassOrObject.constructor == Function )
		{
			//Normal Inheritance
			this.prototype = new parentClassOrObject;
			this.prototype.constructor = this;
			this.prototype.parent = parentClassOrObject.prototype;
		}
		else
		{
			//Pure Virtual Inheritance
			this.prototype = parentClassOrObject;
			this.prototype.constructor = this;
			this.prototype.parent = parentClassOrObject;
		}
		return this;
	}


//*********** BIND CALLBACK ******************
    //lets you pass an object method as a callback to another function, such
    //that that function can store it and call it later with arbitrary parameters
    function bindCallback(toObject, method){
        return function() {  return method.apply(toObject, arguments); }
    }

//************ GEOCODER (REQUIRES GOOGLE MAPS API) ********************
function Geodata(query, latLng, countryCode, countryName, formattedAddress, administrativeArea, thoroughfare, locality, postalCode) {
    this._query = safeString(query);
    this._latLng = defaultIfNotSet(latLng, null);
    this._countryCode = safeString(countryCode);
    this._countryName = safeString(countryName);
    this._formattedAddress = safeString(formattedAddress);
    this._adminArea = safeString(administrativeArea);
    this._thoroughfare = safeString(thoroughfare);
    this._locality = safeString(locality);
    this._postalCode = safeString(postalCode);

    this.getQuery = function() {return this._query}
    this.getLatLng = function() {return this._latLng}
    this.getLat = function() {return this._latLng.lat()}
    this.getLng = function() {return this._latLng.lng()}
    this.getCountryCode = function() {return this._countryCode}
    this.getCountryName = function() {return this._countryName}
    this.getFormattedAddress = function() {return this._formattedAddress}
    this.getAdminArea = function() {return this._adminArea}
    this.getThoroughfare = function() {return this._thoroughfare}
    this.getCity = function() {return this._locality}
    this.getPostalCode = function() {return this._postalCode}

    this.getShorthand = function(hideCountryUS) {
        if (this.hasCity())
        {
            if (hideCountryUS && this._countryName == "USA")
                return [this._locality, this._adminArea].join(", ");
            else
                return [this._locality, this._adminArea, this._countryName].join(", ");
        }
        else if (this.hasAdminArea())
        {
            if (hideCountryUS && this._countryName == "USA")
                return this._adminArea;
            else
                return [this._adminArea, this._countryName].join(", ");
        }
        else if (this.hasCountry())
        {
            return this._formattedAddress;
        }
        else
        {
            return this._query;
        }
    }
    this.getCityStateZip = function() {return [this._locality, this._adminArea, this._postalCode].join(", "); }
    this.hasCity = function() {return (this._locality != "") }
    this.hasData = function() {return (this._latLng != null) }
    this.hasAdminArea = function() {return (this._adminArea != "") }
    this.hasCountry = function() {return (this._countryCode != "") }
}

function Geocoder()
{
	googleCoder = new GClientGeocoder();
	this.geocoding = false;

	this.isGeocoding = function() {return this.geocoding; }
	this.confirmSuccess = function() { this.geocoding = false; clearTimeout(this.geoTimeout); }
	this.timeOut = function() {	this.geocoding = false; clearTimeout(this.geoTimeout); }

	this.geocode = function(query, callback_func)
	{
		this.geocoding = true;
		this.callback_func = callback_func;
		this.activeQuery = query;
		googleCoder.getLocations( query, bindCallback(this, this.geocodeReturn) );
		this.geoTimeout = setTimeout( bindCallback(this, this.timeOut), 15000);
	}
	this.geocodeReturn = function(response)
    {
    	var place, lat, lng;
    	var latLng = countryCode = formattedAddress = administrativeArea = thoroughfare = locality = postalCode = null;

    	if (response && response.Status.code == 200)
    	{
    		place = response.Placemark[0];
    		lat = place.Point.coordinates[1];
    		lng = place.Point.coordinates[0];
    		latLng	= new GLatLng(lat,lng);

    		if (place.AddressDetails.Country)
    		{
    			countryCode = String(place.AddressDetails.Country.CountryNameCode);
    			countryName = String(place.AddressDetails.Country.CountryName);
    			formattedAddress = String(place.address);
    			//store additional information if available
    			if (place.AddressDetails.Country.AdministrativeArea)
    			{

    				if (place.AddressDetails.Country.AdministrativeArea.AdministrativeAreaName)
    				{
    					administrativeArea = String(place.AddressDetails.Country.AdministrativeArea.AdministrativeAreaName);
    				}

    				//for more details, need to see if this area has a SubAdministrativeArea
    				var adminArea = place.AddressDetails.Country.AdministrativeArea;
    				if (place.AddressDetails.Country.AdministrativeArea.SubAdministrativeArea)
    				{
    					adminArea = place.AddressDetails.Country.AdministrativeArea.SubAdministrativeArea
    				}

    				if (adminArea.Locality)
    				{
    					if (adminArea.Locality.Thoroughfare)
    					{
    						thoroughfare = String(adminArea.Locality.Thoroughfare.ThoroughfareName);
    					}

    					if (adminArea.Locality.LocalityName)
    					{
    						locality = String(adminArea.Locality.LocalityName);
    					}

    					if (adminArea.Locality.PostalCode)
    					{
    						postalCode = String(adminArea.Locality.PostalCode.PostalCodeNumber);
    					}
    				}
    			}
    		}
    		var geodata = new Geodata(this.activeQuery, latLng, countryCode, countryName, formattedAddress, administrativeArea, thoroughfare, locality, postalCode);
    	}
    	else
    	{
    	   var geodata = new Geodata(this.activeQuery);
    	}

    	this.activeQuery = "";
    	this.callback_func(geodata);
    }
}


