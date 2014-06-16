# Copyright 2014, Ansible, Inc.
# Luke Sneeringer <lsneeringer@ansible.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import functools
import json

from requests.sessions import Session
from requests.models import Response

from tower_cli.conf import settings
from tower_cli.utils import exceptions as exc


class Client(Session):
    """A class for making HTTP requests to the Ansible Tower API and
    returning the responses.

    This functions as a wrapper around [requests][1], and returns its
    responses; therefore, interact with response objects to this class the
    same way you would with objects you get back from `requests.get` or
    similar.

      [1]: http://docs.python-requests.org/en/latest/
    """
    def __init__(self, host=None):
        """Initialize the API client.

        By default, no server is provided and one is read from settings;
        provide one to override this behavior.
        """
        super(Client, self).__init__()

        # Write the URL prefix to this object.
        host = host or settings.host
        if '://' not in host:
            host = 'https://%s' % host.strip('/')
        self.prefix = '%s/api/v1/' % host.rstrip('/')

    def get_one(self, url, *args, **kwargs):
        """Make a GET request that is intended to return one and exactly one
        result, and complain if it returns zero or 2+.
        """
        # Make the GET request.
        r = self.get(url, *args, **kwargs)
        resp = r.json()

        # Did we get zero results back?
        # If so, this is an error, and we need to complain.
        if resp['count'] == 0:
            raise exc.NotFound('The requested object could not be found.')

        # Did we get more than one result back?
        # If so, this is also an error, and we need to complain.
        if resp['count'] >= 2:
            raise exc.MultipleResults('Expected one result, got %d. Tighten '
                                      'your criteria or use `list`.' %
                                      resp['count'])

        # Done; return the response.
        return r

    @functools.wraps(Session.request)
    def request(self, method, url, *args, **kwargs):
        """Make a request to the Ansible Tower API, and return the
        response.
        """
        # Piece together the full URL.
        url = '%s%s' % (self.prefix, url.lstrip('/'))

        # Ansible Tower expects authenticated requests; add the authentication
        # from settings if it's provided.
        kwargs.setdefault('auth', (settings.username, settings.password))

        # POST and PUT requests will send JSON by default; make this
        # the content_type by default.  This makes it such that we don't have
        # to constantly write that in our code, which gets repetitive.
        headers = kwargs.get('headers', {})
        if method.upper() in ('PATCH', 'POST', 'PUT'):
            headers.setdefault('Content-Type', 'application/json')
            kwargs['headers'] = headers

        # If this is a JSON request, encode the data value.
        if headers.get('Content-Type', '') == 'application/json':
            kwargs['data'] = json.dumps(kwargs.get('data', {}))

        # Call the superclass method.
        r = super(Client, self).request(method, url, *args, **kwargs)

        # Sanity check: Did we fail to authenticate properly?
        # If so, fail out now; this is always a failure.
        if r.status_code == 401:
            raise exc.AuthError('Invalid Tower authentication credentials.')

        # Django REST Framework intelligently prints API keys in the
        # order that they are defined in the models and serializer.
        #
        # We want to preserve this behavior when it is possible to do so
        # with minimal effort, because while the order has no explicit meaning,
        # we make some effort to order keys in a convenient manner.
        #
        # To this end, make this response into an APIResponse subclass
        # (defined below), which has a `json` method that doesn't lose key
        # order.
        r.__class__ = APIResponse

        # Return the response object.
        return r


class APIResponse(Response):
    """A Response subclass which preseves JSON key order (but makes no other
    changes).
    """
    def json(self, **kwargs):
        kwargs.setdefault('object_pairs_hook', collections.OrderedDict)
        return super(APIResponse, self).json(**kwargs)


client = Client()
