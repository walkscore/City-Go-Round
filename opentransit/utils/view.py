import django
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.utils import simplejson as json
from django.http import HttpResponseRedirect, Http404, HttpResponse, HttpResponseBadRequest

def render_to_response(request, template_name, dictionary={}, **kwargs):
    """
    Similar to django.shortcuts.render_to_response, but uses a RequestContext
    with some site-wide context.
    """
    response = django.shortcuts.render_to_response(
        template_name,
        dictionary,
        context_instance=RequestContext(request),
        **kwargs
    )

    return response

def redirect_to(view, *args, **kwargs):
    """
    Similar to urlresolvers.reverse, but returns an HttpResponseRedirect for the
    URL.
    """
    url = reverse(view, args = args, kwargs = kwargs)
    return HttpResponseRedirect(url)
    
def not_implemented(request):
    return render_to_response(request, "not-implemented.html")

def render_image_response(request, image_bytes, mimetype = 'image/png'):
    return HttpResponse(image_bytes, mimetype)

def redirect_to_url(url):
    return HttpResponseRedirect(url)

def bad_request(message = ''):
    return HttpResponseBadRequest(message)
    
def render_to_json(jsonable):
    return HttpResopnse(json.dumps(jsonable), mimetype = 'application/json')
    
def raise_404():
    raise Http404
