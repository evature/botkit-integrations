# -*- coding: utf-8 -*-

import hashlib
from base64 import urlsafe_b64encode
import urlparse
from urllib import quote



class ImagixUrlHelper(object):
    '''Extracted from https://github.com/imgix/imgix-python
    but changed URL encoding to fit with Facebook encoding
    '''
    def __init__(self, domain, path, scheme="https", sign_key=None, opts=None):

        self._scheme = scheme
        self._host = domain
        self._path = path
        self._sign_key = sign_key

        self._parameters = {}
        options = opts or {}
        for key, value in options.iteritems():
            self.set_parameter(key, value)


    def set_parameter(self, key, value):
        if value is None or value is False:
            self.delete_parameter(key)
            return

        if isinstance(value, (int, float)):
            value = str(value)

        if key.endswith('64'):
            value = urlsafe_b64encode(value.encode('utf-8'))
            value = value.replace('=', '')

        self._parameters[key] = value

    def delete_parameter(self, key):
        if key in self._parameters:
            del self._parameters[key]

    def _str_is_ascii(self, s):
        try:
            s.decode('ascii')
            return True
        except:
            return False

    def __str__(self):
        query = {}

        for key in self._parameters:
            query[key] = self._parameters[key]

        path = self._path

        if path.startswith("http"):
            try:
                path = quote(path, safe="")
            except KeyError:
                path = quote(path.encode('utf-8'), safe="")

        if not path.startswith("/"):
            path = "/" + path  # Fix web proxy style URLs

        if not path.startswith("/http") and not self._str_is_ascii(path):
            try:
                path = quote(path)
            except KeyError:
                path = quote(path.encode('utf-8'))

        # replacing %20 with '+' because thats how facebook saves URLs - and it must match in order for the signature to be valid
        query = "&".join(
            (quote(key, "") + "=" + quote(query[key].encode('utf-8'), "").replace('%20','+'))  
            for key in sorted(query))

        if self._sign_key:
            delim = "" if query == "" else "?"
            signing_value = self._sign_key + path + delim + query
            signature = hashlib.md5(signing_value.encode('utf-8')).hexdigest()
            if query:
                query += "&s=" + signature
            else:
                query = "s=" + signature

        return urlparse.urlunparse([
            self._scheme,
            self._host,
            path,
            "",
            query,
            "", ])
