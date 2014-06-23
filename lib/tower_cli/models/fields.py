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

import six


_field_counter = 0


class Field(object):
    """A class representing flags on a given field on a model.
    This class tracks whether a field is unique, filterable, read-only, etc.
    """
    def __init__(self, type=six.text_type, default=None, choices=(),
                       filterable=True, help_text=None, is_option=True,
                       password=False, read_only=False, required=True,
                       show_default=False, unique=False):
        # Save properties of this field.
        self.name = ''
        self.type = type
        self.choices = choices
        self.default = default
        self.help_text = help_text
        self.implicit = False
        self.is_option = is_option
        self.filterable = filterable
        self.password = password
        self.read_only = read_only
        self.required = required
        self.show_default = show_default
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
    def help(self):
        """Return the help text that was passed to the constructor, or a
        sensible default if none was provided.
        """
        if self.help_text:
            return self.help_text
        return 'The %s field.' % self.name

    @property
    def option(self):
        """Return the field name as a bash option string
        (e.g. "--field-name").
        """
        return '--' + self.name.replace('_', '-')


class ImplicitField(Field):
    """A class representing a field that is determined based on values
    provided to other fields, rather than being explicitly set.

    Implicit fields are only calculated for `create` and `modify` commands.
    """
    def __init__(self, help_text=None, required=True):
        self.determine_value = None
        super(ImplicitField, self).__init__(help_text=help_text,
                                            is_option=False, required=required)
        self.implicit = True

    def formula(self, method):
        """Mark a function as being the formula for determining the value
        of this field. That function will be sent a dictionary with the
        data sent from the CLI.

        This method is intended to be used as a decorator.
        """
        self.determine_value = method
        return method

    @property
    def flags(self):
        return 'implicit'
