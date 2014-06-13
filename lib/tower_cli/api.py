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

import functools

from requests.sessions import Session

from tower_cli.conf import settings


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
        if method.upper() in ('POST', 'PUT'):
            headers = kwargs.get('headers', {})
            headers.setdefault('Content-Type', 'application/json')
            kwargs['headers'] = headers

        # Call the superclass method.
        return super(Client, self).request(method, url, *args, **kwargs)


client = Client()
