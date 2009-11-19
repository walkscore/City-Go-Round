from django.http import HttpResponse

def authenticate_request(request, correct_username, correct_password, realm = None):
    """Returns None if the request is authorized with the supplied username/password. Returns an HttpResponse if the request is NOT authorized."""
    authorized = False
    response = None
    
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if (len(auth) == 2) and (auth[0].lower() == 'basic'):
            username, password = auth[1].decode('base64').split(':')
            authorized = (username == correct_username) and (password == correct_password)
                    
    if not authorized:                        
        response = HttpResponse()
        response.status_code = 401
        if realm is None:
            realm = "Web Site"
        response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
        
    return response
