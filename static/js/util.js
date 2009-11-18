// © Front Seat Management 2007

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
			if (addLeadingSpace) str = "x" + str;
			if (addTrailingSpace) str = str + "x";
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
				
