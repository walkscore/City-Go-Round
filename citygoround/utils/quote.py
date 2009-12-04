import urllib

def url_quote(s, charset='utf-8', safe='/:'):
    if isinstance(s, unicode):
        s = s.encode(charset)
    elif not isinstance(s, str):
        s = str(s)
    return urllib.quote(s, safe=safe)

def url_quote_plus(s, charset='utf-8', safe=''):
    if isinstance(s, unicode):
        s = s.encode(charset)
    elif not isinstance(s, str):
        s = str(s)
    return urllib.quote_plus(s, safe=safe)

def url_unquote(s, charset='utf-8', errors='ignore'):
    return urllib.unquote(s).decode(charset, errors)

def url_unquote_plus(s, charset='utf-8', errors='ignore'):
    return urllib.unquote_plus(s).decode(charset, errors)
