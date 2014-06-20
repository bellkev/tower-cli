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
from copy import copy
import functools
import inspect
import json
import re

import six

import click
from click.decorators import _make_command

from tower_cli.api import client
from tower_cli.resources import cli_command
from tower_cli.utils import exceptions as exc
from tower_cli.utils.command import Command
from tower_cli.utils.data_structures import OrderedDict


_field_counter = 0


class Field(object):
    """A class representing flags on a given field on a model.
    This class tracks whether a field is unique, filterable, read-only, etc.
    """
    def __init__(self, type=six.text_type, default=None, filterable=True,
                       password=False, read_only=False, required=True,
                       unique=False):
        # Save properties of this field.
        self.name = ''
        self.type = type
        self.default = default
        self.filterable = filterable
        self.password = password
        self.read_only = read_only
        self.required = required
        self.unique = unique

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

        # Mark all `@cli_command` methods as CLI commands.
        commands = set()
        for base in bases:
            base_commands = getattr(base, 'commands', [])
            commands = commands.union(base_commands)
        for key, value in attrs.items():
            if getattr(value, '_cli_command', False):
                commands.add(key)
        attrs['commands'] = sorted(commands)

        # Sanity check: Only perform remaining initialization for subclasses
        # of Resource, not Resource itself.
        parents = [b for b in bases if isinstance(b, ResourceMeta)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        # Initialize a new attributes dictionary.
        newattrs = {}

        # Iterate over each of the fields and move them into a
        # `fields` list; port remaining attrs unchanged into newattrs.
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
        if not newattrs.get('endpoint', None):
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
    cli_help = ''
    endpoint = None

    # The basic methods for interacting with a resource are `read`, `write`,
    # and `delete`; these cover basic CRUD situations and have options
    # to handle most desired behavior.
    #
    # Most likely, `read` and `write` won't see much direct use; rather,
    # `get` and `list` are wrappers around `read` and `create` and
    # `modify` are wrappers around `write`.

    def as_command(self):
        """Return a `click.Command` class for interacting with this
        Resource.
        """
        class Subcommand(click.MultiCommand):
            """A subcommand that implements all command methods on the
            Resource.
            """
            def __init__(self, resource, *args, **kwargs):
                self.resource = resource
                self.resource_name = resource.__module__.split('.')[-1]
                super(Subcommand, self).__init__(*args,
                    help=self.resource.cli_help,
                    **kwargs
                )

            def list_commands(self, ctx):
                """Return a list of all methods decorated with the
                @cli_command decorator.
                """
                return self.resource.commands

            def get_command(self, ctx, name):
                """Retrieve the appropriate method from the Resource,
                decorate it as a click command, and return that method.
                """
                # Get the method.
                method = getattr(self.resource, name)

                # If the help message comes from the docstring, then
                # convert it into a message specifically for this resource.
                attrs = getattr(method, '_cli_command_attrs', {})
                help_text = inspect.getdoc(method)
                if isinstance(help_text, six.binary_type):
                    help_text = help_text.decode('utf-8')
                attrs['help'] = self._auto_help_text(help_text)

                # Wrap the method, such that it outputs its final return
                # value rather than returning it.
                new_method = self._echo_method(method)

                # Soft copy the "__click_params__", if any exist.
                # This is the internal holding method that the click library
                # uses to store @click.option and @click.argument directives
                # before the method is converted into a command.
                #
                # Because self._echo_method uses @functools.wraps, this is
                # actually preserved; the purpose of copying it over is
                # so we can get our resource fields at the top of the help;
                # the easiest way to do this is to load them in before the
                # conversion takes place. (This is a happy result of Armin's
                # work to get around Python's processing decorators
                # bottom-to-top.)
                click_params = getattr(method, '__click_params__', [])
                new_method.__click_params__ = copy(click_params)

                # Write options based on the fields available on this resource.
                for field in reversed(self.resource.fields):
                    click.option(field.option, type=field.type,
                                 help='The %s field.' % field.name)(new_method)

                # Make a click Command instance using this method
                # as the callback, and return it.
                command = _make_command(new_method, name=name, attrs=attrs,
                                                    cls=Command)

                # If this method has a `pk` positional argument,
                # then add a click argument for it.
                code = six.get_function_code(method)
                if 'pk' in code.co_varnames:
                    click.argument('pk', nargs=1, required=False,
                                         type=int)(command)

                # Done; return the command.
                return command

            def _auto_help_text(self, help_text):
                """Given a method with a docstring, convert the docstring
                to more CLI appropriate wording, and also disambiguate the
                word "object" on the base class docstrings.
                """
                # Convert the word "object" to the appropriate type of
                # object being modified (e.g. user, organization).
                if not self.resource_name.startswith(('a', 'e', 'i', 'o')):
                    help_text = help_text.replace('an object',
                                                  'a %s' % self.resource_name)
                help_text = help_text.replace('object', self.resource_name)

                # Convert some common Python terms to their CLI equivalents.
                help_text = help_text.replace('keyword argument', 'option')
                help_text = help_text.replace('raise an exception',
                                              'abort with an error')

                # Convert keyword arguments specified in docstrings enclosed
                # by backticks to switches.
                for match in re.findall(r'`([\w_]+)`', help_text):
                    option = '--%s' % match.replace('_', '-')
                    help_text = help_text.replace('`%s`' % match, option)

                # Done; return the new help text.
                return help_text

            def _echo_method(self, method):
                """Given a method, return a method that runs the internal
                method and echos the result.
                """
                @functools.wraps(method)
                def func(*args, **kwargs):
                    result = method(*args, **kwargs)

                    # If this was a request that could result in a modification
                    # of data, print it in Ansible coloring.
                    color_info = {}
                    if 'changed' in result:
                        if result['changed']:
                            color_info['fg'] = 'yellow'
                        else:
                            color_info['fg'] = 'green'

                    # Perform the echo.
                    click.secho(json.dumps(result, indent=2), **color_info)
                return func

        return Subcommand(resource=self)

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

        # Remove default values (anything where the value is None).
        # click is unfortunately bad at the way it sends through unspecified
        # defaults.
        for key, value in copy(kwargs).items():
            if value is None:
                kwargs.pop(key)
            if hasattr(value, 'read'):
                kwargs[key] = value.read()

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

        # Sanity check: Are we missing required values?
        # If we don't have a primary key, then all required values must be
        # set, and if they're not, it's an error.
        required_fields = [i.name for i in self.fields if i.required]
        missing_fields = [i for i in required_fields if i not in kwargs]
        if missing_fields:
            raise exc.BadRequest('Missing required fields: %s' %
                                 ', '.join(missing_fields))

        # Sanity check: Do we need to do a write at all?
        # If `force_on_exists` is False and the record was, in fact, found,
        # then no action is required.
        if pk and not force_on_exists:
            return OrderedDict((
                ('changed', False),
                ('id', pk),
            ))

        # Similarly, if all existing data matches our write parameters,
        # there's no need to do anything.
        if all([kwargs[k] == existing_data.get(k, None)
                for k in kwargs.keys()]):
            return OrderedDict((
                ('changed', False),
                ('id', pk),
            ))

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
        return OrderedDict((
            ('changed', True),
            ('id', r.json()['id']),
        ))

    @cli_command(no_args_is_help=True)
    def delete(self, pk=None, fail_on_missing=False, **kwargs):
        """Remove the given object.

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

    @cli_command(no_args_is_help=True)
    def get(self, pk=None, **kwargs):
        """Return one and exactly one object.

        Lookups may be through a primary key, specified as a positional
        argument, and/or through filters specified through keyword arguments.

        If the number of results does not equal one, raise an exception.
        """
        response = self.read(pk=pk, fail_on_no_results=True,
                             fail_on_multiple_results=True, **kwargs)
        return response['results'][0]

    @cli_command
    @click.option('--page', default=1, type=int, help='The page to show.',
                            show_default=True)
    def list(self, **kwargs):
        """Return a list of objects.

        If one or more filters are provided through keyword arguments,
        filter the results accordingly.

        If no filters are provided, return all results.
        """
        # Get the response.
        response = self.read(**kwargs)

        # Alter the "next" and "previous" to reflect simple integers,
        # rather than URLs, since this endpoint just takes integers.
        for key in ('next', 'previous'):
            if not response[key]:
                continue
            match = re.search(r'page=(?P<num>[\d]+)', response[key])
            response[key] = int(match.groupdict()['num'])

        # Done; return the response
        return response

    @cli_command(no_args_is_help=True)
    @click.option('--fail-on-found', default=False,
                  show_default=True, type=bool,
                  help='If True, return an error if a matching record already '
                       'exists.')
    @click.option('--force-on-exists', default=False,
                  show_default=True, type=bool,
                  help='If True, if a match is found on unique fields, other '
                       'fields will be updated to the provided values. If '
                       'False, a match causes the request to be a no-op.')
    def create(self, fail_on_found=False, force_on_exists=False, **kwargs):
        """Create an object.

        If unique fields exist and all unique fields are provided, and a match
        is found, then no-op (unless `force_on_exists` is True) but do not
        fail (unless `fail_on_found` is True).
        """
        return self.write(create_on_missing=True, fail_on_found=fail_on_found,
                          force_on_exists=force_on_exists, **kwargs)

    @cli_command(no_args_is_help=True)
    @click.option('--create-on-missing', default=False,
                  show_default=True, type=bool,
                  help='If True, and if options rather than a primary key are '
                       'used to attempt to match a record, will create the '
                       'record if it does not exist. This is an alias to '
                       '`create --force-on-exists=true`.')
    def modify(self, pk=None, create_on_missing=False, **kwargs):
        """Modify an already existing object.

        If unique fields exist and are provided, they can be used in lieu of
        a primary key for a lookup; in such a case, only non-unique fields
        are written.

        To modify unique fields, you must use the primary key for the lookup.
        """
        return self.write(pk, create_on_missing=create_on_missing,
                              force_on_exists=True, **kwargs)

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
