from django.conf import settings

def appengine_user(request):
    if request.user:
        return {'user': request.user, 'user_is_valid':request.user.is_valid}
    else:
        return {'user': None, 'user_is_valid':False}


def api_keys(request):
    return {'GOOGLE_API_KEY': settings.GOOGLE_API_KEY}
    