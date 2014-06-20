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

from __future__ import absolute_import, unicode_literals

import six

from tower_cli.api import client
from tower_cli.utils import exceptions as exc


_field_counter = 0


class Field(object):
    """A class representing flags on a given field on a model.
    This class tracks whether a field is unique, filterable, read-only, etc.
    """
    def __init__(self, type=six.text_type, default=None, filterable=True,
                       unique=False, read_only=False, required=True):
        # Save properties of this field.
        self.name = ''
        self.type = type
        self.default = default
        self.filterable = filterable
        self.unique = unique
        self.read_only = read_only
        self.required = required

        # Track the creation history of each field, for sorting reasons.
        global _field_counter
        self.number = _field_counter
        _field_counter += 1

    def __lt__(self, other):
        return self.number < other.number

    def __gt__(self, other):
        return self.number > other.number

    def __repr__(self):
        return '<Field: %s (%s)>' % (self.name, self.flags)

    @property
    def flags(self):
        flags_list = [self.type.__name__]        
        if self.read_only:
            flags_list.append('read-only')
        if self.unique:
            flags_list.append('unique')
        if not self.filterable:
            flags_list.append('not filterable')
        if not self.required:
            flags_list.append('not required')
        return ', '.join(flags_list)

    @property
    def option(self):
        """Return the field name as a bash option string
        (e.g. "--field-name").
        """
        return '--' + self.name.replace('_', '-')


class ResourceMeta(type):
    """Metaclass for the creation of a Model subclass, which pulls fields
    aside into their appropriate tuple and handles other initialization.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(ResourceMeta, cls).__new__

        # Sanity check: Only perform initialization for subclasses.
        parents = [b for b in bases if isinstance(b, ResourceMeta)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        # Initialize a new attributes dictionary.
        newattrs = {}

        # Iterate over each of the fields and move them into a
        # `fields` list.
        fields = []
        unique_fields = set()
        for k, v in attrs.items():
            if isinstance(v, Field):
                v.name = k
                fields.append(v)
                if v.unique:
                    unique_fields.add(v.name)
            else:
                newattrs[k] = v
        newattrs['fields'] = sorted(fields)
        newattrs['unique_fields'] = unique_fields

        # Cowardly refuse to create a Resource with no endpoint
        # (unless it's the base class).
        if 'endpoint' not in newattrs:
            raise TypeError('Resource subclasses must have an `endpoint`.')

        # Ensure that the endpoint ends in a trailing slash, since we
        # expect this when we build URLs based on it.
        if not newattrs['endpoint'].endswith('/'):
            newattrs['endpoint'] += '/'

        # Construct the class.
        return super_new(cls, name, bases, newattrs)


class Resource(six.with_metaclass(ResourceMeta)):
    """Abstract class representing resources within the Ansible Tower system,
    on which actions can be taken.
    """
    endpoint = None

    # The basic methods for interacting with a resource are `read`, `write`,
    # and `delete`; these cover basic CRUD situations and have options
    # to handle most desired behavior.
    #
    # Most likely, `read` and `write` won't see much direct use; rather,
    # `get` and `list` are wrappers around `read` and `create` and
    # `modify` are wrappers around `write`.

    def read(self, pk=None, fail_on_no_results=False, 
                   fail_on_multiple_results=False, **kwargs):
        """Retrieve and return objects from the Ansible Tower API.

        If an `object_id` is provided, only attempt to read that object,
        rather than the list at large.

        If `fail_on_no_results` is True, then zero results is considered
        a failure case and raises an exception; otherwise, empty list is
        returned. (Note: This is always True if a primary key is included.)

        If `fail_on_multiple_results` is True, then at most one result is
        expected, and more results constitutes a failure case.
        (Note: This is meaningless if a primary key is included, as there can
        never be multiple results.)
        """
        # Piece together the URL we will be hitting.
        url = self.endpoint
        if pk:
            url += '%d/' % pk

        # Make the request to the Ansible Tower API.
        r = client.get(url, params=kwargs)
        resp = r.json()

        # If this was a request with a primary key included, then at the
        # point that we got a good result, we know that we're done and can
        # return the result.
        if pk:
            # Make the results all look the same, for easier parsing
            # by other methods.
            #
            # Note that the `get` method will effectively undo this operation,
            # but that's a good thing, because we might use `get` without a
            # primary key.
            return {'count': 1, 'results': [resp]}

        # Did we get zero results back when we shouldn't?
        # If so, this is an error, and we need to complain.
        if fail_on_no_results and resp['count'] == 0:
            raise exc.NotFound('The requested object could not be found.')

        # Did we get more than one result back?
        # If so, this is also an error, and we need to complain.
        if fail_on_multiple_results and resp['count'] >= 2:
            raise exc.MultipleResults('Expected one result, got %d. Tighten '
                                      'your criteria.' % resp['count'])

        # Return the response.
        return resp

    def write(self, pk=None, create_on_missing=False, fail_on_found=False,
                    force_on_exists=True, **kwargs):
        """Modify the given object using the Ansible Tower API.
        Return the object and a boolean value informing us whether or not
        the record was changed.

        If `create_on_missing` is True, then an object matching the
        appropriate unique criteria is not found, then a new object is created.

        If there are no unique criteria on the model (other than the primary
        key), then this will always constitute a creation (even if a match
        exists) unless the primary key is sent.

        If `fail_on_found` is True, then if an object matching the unique
        criteria already exists, the operation fails.

        If `force_on_exists` is True, then if an object is modified based on
        matching via. unique fields (as opposed to the primary key), other
        fields are updated based on data sent. If `force_on_exists` is set
        to False, then the non-unique values are only written in a creation
        case.
        """
        existing_data = {}

        # Determine which record we are writing, if we weren't given a
        # primary key.
        if not pk:
            existing_data = self._lookup(
                fail_on_found=fail_on_found,
                fail_on_missing=not create_on_missing,
                **kwargs
            )
            if existing_data:
                pk = existing_data['id']
        else:
            # We already know the primary key, but get the existing data.
            # This allows us to know whether the write made any changes.
            existing_data = self.get(pk)

        # Sanity check: Do we need to do a write at all?
        # If `force_on_exists` is False and the record was, in fact, found,
        # then no action is required.
        if pk and not force_on_exists:
            return {'changed': False, 'id': pk}

        # Similarly, if all existing data matches our write parameters,
        # there's no need to do anything.
        if all([kwargs[k] == existing_data.get(k, None)
                for k in kwargs.keys()]):
            return {'changed': False, 'id': pk}

        # Get the URL and method to use for the write.
        url = self.endpoint
        method = 'POST'
        if pk:
            url += '%d/' % pk
            method = 'PATCH'

        # Actually perform the write.
        r = getattr(client, method.lower())(url, data=kwargs)

        # At this point, we know the write succeeded, and we know that data
        # was changed in the process.
        return {'changed': True, 'id': r.json()['id']}

    def delete(self, pk=None, fail_on_missing=False, **kwargs):
        """Remove the given object using the Ansible Tower API.

        If `fail_on_missing` is True, then the object's not being found is
        considered a failure; otherwise, a success with no change is reported.
        """
        # If we weren't given a primary key, determine which record we're
        # deleting.
        if not pk:
            existing_data = self._lookup(fail_on_missing=fail_on_missing,
                                         **kwargs)
            if not existing_data:
                return {'changed': False}
            pk = existing_data['id']

        # Attempt to delete the record.
        # If it turns out the record doesn't exist, handle the 404
        # appropriately (this is an okay response if `fail_on_missing` is
        # False).
        url = '%s%d/' % (self.endpoint, pk)
        try:
            client.delete(url)
            return {'changed': True}
        except exc.NotFound:
            if fail_on_missing:
                raise
            return {'changed': False}

    # Convenience wrappers around `read` and `write`:
    #   - read:  get, list
    #   - write: create, modify

    def get(self, pk=None, fail_on_no_results=True,
                  fail_on_multiple_results=True, **kwargs):
        """Return the one and exactly one result that matches the provided
        primary key and/or filters.

        If the number of results does not equal one, raise an exception.
        """
        response = self.read(pk=pk, fail_on_no_results=True,
                             fail_on_multiple_results=True, **kwargs)
        return response['results'][0]

    def list(self, **kwargs):
        """Return a list of objects matching the provided filters.
        If no filters are provided, return all results.
        """
        return self.read(**kwargs)

    def create(self, fail_on_found=False, force_on_exists=False, **kwargs):
        """Create an object.

        If unique fields exist and all unique fields are provided, and a match
        is found, then no-op (unless `force_on_exists` is True) but do not
        fail (unless `fail_on_found` is True).
        """
        return self.write(create_on_missing=True, fail_on_found=fail_on_found,
                          force_on_exists=force_on_exists, **kwargs)

    def modify(self, pk=None, create_on_missing=False, force_on_exists=True,
                     **kwargs):
        """Modify an already existing object.

        If unique fields exist and all unique fields are provided, they can be
        used in lieu of a primary key for a lookup; in such a case, only
        non-unique fields are written.
        """
        return self.write(pk, create_on_missing=create_on_missing,
                              force_on_exists=force_on_exists, **kwargs)

    def _lookup(self, fail_on_missing=False, fail_on_found=False, **kwargs):
        """Attempt to perform a lookup that is expected to return a single
        result, and return the record.

        This method is a wrapper around `get` that strips out non-unique
        keys, and is used internally by `write` and `delete`.
        """
        # Determine which parameters we are using to determine
        # the appropriate field.
        read_params = {}
        for unique_field in self.unique_fields:
            if unique_field in kwargs:
                read_params[unique_field] = kwargs[unique_field]

        # Sanity check: Do we have any parameters?
        # If not, then there's no way for us to do this read.
        if not read_params:
            raise exc.BadRequest('Cannot reliably determine which record '
                                 'to write. Include an ID or unique '
                                 'fields.')

        # Get the record to write.
        try:
            existing_data = self.get(**read_params)
            if fail_on_found:
                raise exc.Found('A record matching %s already exists, and '
                                'you requested a failure in that case.')
            return existing_data
        except exc.NotFound as ex:
            if fail_on_missing:
                raise
            return {}
