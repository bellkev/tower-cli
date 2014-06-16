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
        newattrs = {}
        fields = []
        for k, v in attrs.items():
            if isinstance(v, Field):
                v.name = k
                fields.append(v)
            else:
                newattrs[k] = v
        newattrs['fields'] = sorted(fields)
        return super(ModelMeta, cls).__new__(cls, name, bases, newattrs)


class Resource(six.with_metaclass(ResourceMeta)):
    """Abstract class representing resources within the Ansible Tower system,
    on which actions can be taken.
    """
    endpoint = NotImplemented

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
        returned.

        If `fail_on_multiple_results` is True, then at most one result is
        expected, and more results constitutes a failure case.
        """

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

    def delete(self, pk, fail_on_missing=False):
        """Remove the given object using the Ansible Tower API.

        If `fail_on_missing` is True, then the object's not being found is
        considered a failure; otherwise, a success with no change is reported.
        """

    # Convenience wrappers around `read` and `write`:
    #   - read:  get, list
    #   - write: create, modify

    def get(self, pk=None, fail_on_no_results=True,
                  fail_on_multiple_results=True, **kwargs):
        """Return the one and exactly one result that matches the provided
        primary key and/or filters.

        If the number of results does not equal one, raise an exception.
        """
        return self.read(pk=pk, fail_on_no_results=fail_on_no_results,
                         fail_on_multiple_results=fail_on_multiple_results,
                         **kwargs)

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

