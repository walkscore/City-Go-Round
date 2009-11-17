import logging

from django.http import Http404
from ..models import TransitApp


def requires_valid_slug(func):
    def wrapper(request, transit_app_slug, *args, **kwargs):
        transit_app = TransitApp.transit_app_for_slug(transit_app_slug)
        if transit_app is not None:
            return func(request, transit_app, *args, **kwargs)
        else:
            raise Http404
    return wrapper