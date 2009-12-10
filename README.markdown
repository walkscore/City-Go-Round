CityGoRound.org
===============

[City-Go-Round](http://www.citygoround.org/) makes it easy for you to discover great new apps that help you get around town.

By showcasing innovation in transit apps, we hope that [City-Go-Round](http://www.citygoround.org/) will encourage your favorite local transit agency to make its data open and publicly available.

TECHNOLOGY
----------

This repository contains all the code and assets that power [http://citygoround.org/](http://www.citygoround.org/). The site runs on Google AppEngine and uses Django 1.1.

This code is released under the BSD license. Do what you will with it. 

(There are a few third-party libraries checked into this repository. They are licensed separately. See the individual license files for details, or in some cases comments at the top of each file.)


HOW TO GET RUNNING LOCALLY
--------------------------

If you want to run this application locally, follow these easy steps:

1. Make sure you have Python 2.5 installed

	If you use a Mac with MacPorts, you can use python_select to choose python 2.5. Unforuntately, as of this writing, AppEngine does not support Python 2.6.
   
2. Install Django 1.1. 

	Unfortunately, the AppEngine development server does not like virtualenv, etc. So you'll have to install django 1.1 as a major package. easy_install is a good way to go.

3. Install the [App Engine Python SDK](http://code.google.com/appengine/downloads.html#Google_App_Engine_SDK_for_Python).

4. `cd` into this directory and run `dev_appserver.py .` to get the local server running.

5. Test by visiting `http://localhost:8080/`
