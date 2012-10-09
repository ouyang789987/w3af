'''
HTTPRequestParser.py

Copyright 2008 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
import urlparse

from core.data.parsers.urlParser import url_object
from core.data.dc.header import Header
from core.data.request.factory import create_fuzzable_request
from core.controllers.w3afException import w3afException


def checkVersionSyntax(version):
    '''
    @return: True if the syntax of the version section of HTTP is valid; else raise an exception.

    >>> checkVersionSyntax('HTTP/1.0')
    True

    >>> checkVersionSyntax('HTTPS/1.0')
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    w3afException: The HTTP request has an invalid HTTP token in the version specification: "HTTPS/1.0"

    >>> checkVersionSyntax('HTTP/1.00000000000000')
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    w3afException: HTTP request version "HTTP/1.00000000000000" is unsupported

    >>> checkVersionSyntax('ABCDEF')
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    w3afException: The HTTP request has an invalid version token: "ABCDEF"
    '''
    supportedVersions = ['1.0', '1.1']
    splittedVersion = version.split('/')

    if len(splittedVersion) != 2:
        msg = 'The HTTP request has an invalid version token: "' + version +'"'
        raise w3afException(msg)
    elif len(splittedVersion) == 2:
        if splittedVersion[0].lower() != 'http':
            msg = 'The HTTP request has an invalid HTTP token in the version specification: "'
            msg += version + '"'
            raise w3afException(msg)
        if splittedVersion[1] not in supportedVersions:
            raise w3afException('HTTP request version "' + version + '" is unsupported')
    return True

def checkURISyntax(uri, host=None):
    '''
    @return: True if the syntax of the URI section of HTTP is valid; else raise an exception.

    >>> checkURISyntax('http://abc/def.html')
    'http://abc/def.html'

    >>> checkURISyntax('ABCDEF')
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    w3afException: You have to specify the complete URI, including the protocol and the host. Invalid URI: ABCDEF
    '''
    supportedSchemes = ['http', 'https']
    scheme, domain, path, params, qs, fragment = urlparse.urlparse(uri)

    if not scheme:
        scheme = 'http'
    if not domain:
        domain = host
    if not path:
        path = '/'

    if scheme not in supportedSchemes or not domain:
        msg = 'You have to specify the complete URI, including the protocol and the host.'
        msg += ' Invalid URI: ' + uri
        raise w3afException(msg)

    res = urlparse.urlunparse( (scheme, domain, path, params, qs, fragment) )
    return res

def HTTPRequestParser(head, postdata):
    '''
    This function parses HTTP Requests from a string to a fuzzable_request.
    
    @parameter head: The head of the request.
    @parameter postdata: The post data of the request
    @return: A fuzzable_request object with all the corresponding information
        that was sent in head and postdata
    
    @author: Andres Riancho (andres.riancho@gmail.com)

    '''
    # Parse the request head
    splitted_head = head.split('\n')
    splitted_head = [h.strip() for h in splitted_head if h]
    
    if not splitted_head:
        msg = 'The HTTP request is invalid.'
        raise w3afException(msg)        
    
    # Get method, uri, version
    method_uri_version = splitted_head[0]
    first_line = method_uri_version.split(' ')
    if len(first_line) == 3:
        # Ok, we have something like "GET /foo HTTP/1.0". This is the best case for us!
        method, uri, version = first_line
    elif len(first_line) < 3:
        msg = 'The HTTP request has an invalid <method> <uri> <version> token: "'
        msg += method_uri_version +'".'
        raise w3afException(msg)
    elif len(first_line) > 3:
        # GET /hello world.html HTTP/1.0
        # Mostly because we are permissive... we are going to try to send the request...
        method = first_line[0]
        version = first_line[-1]
        uri = ' '.join( first_line[1:-1] )
    
    checkVersionSyntax(version)
    
    # If we got here, we have a nice method, uri, version first line
    # Now we parse the headers (easy!) and finally we send the request
    headers = splitted_head[1:]
    headers_dict = {}
    for header in headers:
        one_splitted_header = header.split(':', 1)
        if len(one_splitted_header) == 1:
            raise w3afException('The HTTP request has an invalid header: "' + header + '"')
        
        header_name = one_splitted_header[0].strip()
        header_value = one_splitted_header[1].strip()
        if header_name in headers_dict:
            headers_dict[header_name].append(header_value)
        else:
            headers_dict[header_name] = [header_value,]

    headers = Header(headers_dict.items())

    host = ''
    for header_name in headers_dict:
        if header_name.lower() == 'host':
            host = headers_dict[header_name]
    uri = url_object(checkURISyntax(uri, host))
    
    return create_fuzzable_request(uri, method, postdata, headers)
