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

import copy
import os
import warnings

from six.moves import configparser
from six import StringIO


class Parser(configparser.ConfigParser):
    """ConfigParser subclass that doesn't strictly require section
    headers.
    """
    def _read(self, fp, fpname):
        """Read the configuration from the given file.

        If the file lacks any section header, add a [general] section
        header that encompasses the whole thing.
        """
        # Attempt to read the file using the superclass implementation.
        #
        # If it doesn't work because there's no section header, then
        # create a section header and call the superclass implementation
        # again.
        try:
            return configparser.ConfigParser._read(self, fp, fpname)
        except configparser.MissingSectionHeaderError:
            fp.seek(0)
            string = '[general]\n%s' % fp.read()
            flo = StringIO(string)  # flo == file-like object
            return configparser.ConfigParser._read(self, flo, fpname)


class Settings(object):
    """An object that understands permanent configuration provided to
    tower-cli through configuration files or command-line arguments.

    The order of precedence for settings, from least to greatest, is:

        - `/etc/awx/tower_cli.cfg`
        - `~/.tower_cli.cfg`
        - command line arguments
        - defaults provided in this method

    """
    def __init__(self):
        """Create the settings object, and read from appropriate files as
        well as from `sys.argv`.
        """
        self._cache = {}

        # Initialize the data dictionary for the default level
        # precedence (that is, the bottom of the totem pole).
        defaults = {
            'auth_token': None,
            'color': True,
            'host': '127.0.0.1',
            'password': None,
            'username': None,
        }

        # If there is a global settings file, initialize it.
        self._global = Parser(defaults=defaults)
        self._global.add_section('general')
        if os.path.isdir('/etc/awx/'):
            # Sanity check: Try to actually get a list of files in `/etc/awx/`.
            # 
            # The default Tower installation caused `/etc/awx/` to have
            # extremely restrictive permissions, since it has its own user
            # and group and has a chmod of 0750.
            #
            # This makes it very easy for a user to fall into the mistake
            # of writing a config file under sudo which they then cannot read,
            # which could lead to difficult-to-troubleshoot situations.
            #
            # Therefore, check for that particular problem and give a warning
            # if we're in that situation.
            try:
                global_settings = 'tower_cli.cfg' in os.listdir('/etc/awx/')
            except OSError:
                warnings.warn('/etc/awx/ is present, but not readable with '
                              'current permissions. Any settings defined in '
                              '/etc/awx/tower_cli.cfg will not be honored.',
                              RuntimeWarning)

            # If there is a global settings file for Tower CLI, read in its
            # contents.
            self._global.read('/etc/awx/tower_cli.cfg')

        # Initialize a parser for the user settings file.
        self._user = Parser()
        self._user.add_section('general')

        # If there is a user settings file, read it into the parser
        # object.
        user_filename = os.path.expanduser('~/.tower_cli.cfg')
        if os.path.isfile(user_filename):
            self._user.read(user_filename)

        # FIXME:
        # Determine a way to consume common settings sent directly
        # to the CLI at this point, including getting them actually consumed
        # and removed from `sys.argv`.
        self._runtime = Parser()
        self._runtime.add_section('general')

    def __getattr__(self, key):
        """Return the approprate value, intelligently type-casted in the
        case of numbers or booleans.
        """
        # Sanity check: Have I cached this value? If so, return that.
        if key in self._cache:
            return self._cache[key]

        # Run through each of the parsers and check for a value. Whenever
        # we actually find a value, try to determine the correct type for it
        # and cache and return a value of that type.
        parsers = (self._global, self._user, self._runtime)
        for parser in parsers:
            # Get the value from this parser; if it's None, then this
            # key isn't present and we move on to the next one.
            value = parser.get('general', key, fallback=None)
            if value is None:
                continue

            # We have a value; it may or may not be a string, though, so
            # try to return it as an int, float, or boolean (in that order)
            # before falling back to the string value.
            type_method = ('getint', 'getfloat', 'getboolean')
            for tm in type_method:
                try:
                    value = getattr(parser, tm)('general', key)
                    break
                except ValueError:
                    pass

            # Write the value to the cache, so we don't have to do this lookup
            # logic on subsequent requests.
            self._cache[key] = value
            return self._cache[key]

        # If we got here, that means that the attribute wasn't found, and
        # also that there is no default; raise an exception.
        raise AttributeError('No setting exists: %s.' % key.lower())


# The primary way to interact with settings is to simply hit the
# already constructed settings object.
settings = Settings()
