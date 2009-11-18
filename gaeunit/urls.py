# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('gaeunit.gaeunit', 
    url(r'/run', 'django_json_test_runner'), 
    url('.*', 'django_test_runner'),
)
