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
import collections
import os
import re

import click

import tower_cli
from tower_cli.utils import exceptions as exc


class File(click.File):
    """A subclass of click.File that adds `os.path.expanduser`."""

    __name__ = 'file'

    def convert(self, value, param, ctx):
        if hasattr(value, 'read') or hasattr(value, 'write'):
            return value
        value = os.path.expanduser(value)
        return super(File, self).convert(value, param, ctx)


class MappedChoice(click.Choice):
    """A subclass of click.Choice that allows a distinction between the
    choice sent to the method and the choice typed on the CLI.
    """
    def __init__(self, choices):
        super(MappedChoice, self).__init__()
        choices = collections.OrderedDict(choices)

        # Call the values list "choices" so we take advantage of the
        # superclass functionality.
        self.choices = [i for i in choices.values()]
        self.actual_choices = [i for i in choices.keys()]

    def convert(self, value, param, ctx):
        """Match against the appropriate choice value using the superclass
        implementation, and then return the actual choice.
        """
        choice = super(MappedChoice, self).convert(value, param, ctx)
        ix = self.choices.index(choice)
        return self.actual_choices[ix]


class Related(click.types.ParamType):
    """A subclass of click.types.ParamType that represents a value
    related to another resource.
    """
    name = 'related'

    def __init__(self, resource_name, criterion='name'):
        super(Related, self).__init__()
        self.resource = tower_cli.get_resource(resource_name)
        self.resource_name = resource_name
        self.criterion = criterion

    def convert(self, value, param, ctx):
        """Return the appropriate interger value. If a non-integer is
        provided, attempt a name-based lookup and return the primary key.
        """
        # Ensure that None is passed through without trying to
        # do anything.
        if value is None:
            return None

        # If we were already given an integer, do nothing.
        # This ensures that the convert method is idempotent.
        if isinstance(value, int):
            return value

        # Do we have a string that contains only digits?
        # If so, then convert it to an integer and return it.
        if re.match(r'^[\d]+$', value):
            return int(value)

        # Okay, we have a string. Try to do a name-based lookup on the
        # resource, and return back the ID that we get from that.
        #
        # This has the chance of erroring out, which is fine.
        try:
            rel = self.resource.get(**{self.criterion: value})
        except exc.TowerCLIError as ex:
            raise exc.RelatedError('Could not get %s. %s' %
                                   (self.resource_name, str(ex)))

        # Done! Return the ID.
        return rel['id']

    def get_metavar(self, param):
        return self.resource_name.upper()
