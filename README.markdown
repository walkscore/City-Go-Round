TransitData.org
===================

The following repository contains all the code to power the [Transit Data](http://transitdata.org/) web site.

It is an AppEngine application running Django 1.1.

It is released under BSD -- do what you will with it.


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




A BIT ABOUT DJANGO ON APPENGINE
-------------------------------

If you look at `bootstrap.py` you'll see that it loads the Django 1.1 library (which is pre-installed on the AppEngine servers) and does a few things to load in `settings.py`.

The `opentransit` directory is the django "application." It is where all the *real* work of this application is going to get done. Chances are, if you want to write some code, you want to write it here.

The top-level `urls.py` file simply loads URLs from `opentransit/urls.py`. Any time you add a view (in `opentransit/views.py`) you should also add a new url in `opentransit/urls.py`.

We also have top-level `static` and `templates` directories. The `static` directory is for truly static files, like images, javascript, and CSS. You can reference these cleanly in your django templates with `{% static_url /images/foo.png %}`. The `templates` directory contains Django 1.1-syntax templates. I put in an example `base.html`	and `home.html` file which makes use of Django's `{% extends ... %}` template tag. This is the way most people do things with Django but it is by no means required. These are example files only!

So, again, everything interesting code-wise is going to be under the `opentransit/` subdirectory. Most interesting are `views.py`, where you put your view functions, and `models.py`, where you put your AppEngine model classes. Easy, right? `forms.py` might also be interesting if we decide to use Django forms to handle our petition, etc. Django forms are not required, but they're easy to work with. I already added a petition example just to get us going.

I have also added a bunch of "helper" code in case we want to do more interesting things. Included in the `opentransit` directory are:

1. Some new template tags:

	`static_url` makes it easy to reference stuff in our `static` top level directory

	`partial` is just like Django 1.1's include, except you can pass a state dictionary down to the included file. 

2. Some code to help us with login/logout of users.

	My guess is that we will not need this code, which is spread across `utils.py`, `middleware.py` and `context.py`. You can happily ignore these files unless we decide we want users on AppEngine.

3. A simple, example Django form.

	Again, we don't have to use Django forms. But it may be nice to do so. So I put an example in `forms.py`

4. A simple, example AppEngine mdoel.

	This really is an AppEngine model, not a Django model. We can't use Django models when running on AppEngine.

5. Two simple, example views.

	The corresponding templates link to one another using the `{% url ... %}` template tag.

Let me know if you have any questions. -- Dave



