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

import click
from click._compat import get_text_stderr


class TowerCLIError(click.ClickException):
    """Base exception class for problems raised within Tower CLI.
    This class adds coloring to exceptions.
    """
    fg = 'red'
    bg = None
    bold = True

    def show(self, file=None):
        if file is None:
            file = get_text_stderr()
        click.secho('Error: %s' % self.format_message(), file=file,
                    fg=self.fg, bg=self.bg, bold=self.bold)


class AuthError(TowerCLIError):
    """An exception class for reporting when a request failed due to an
    authorization failure.
    """
    exit_code = 16


class NotFound(TowerCLIError):
    """An exception class for reporting when a request went through without
    incident, but the requested content could not be found.
    """
    exit_code = 4


class MultipleResults(TowerCLIError):
    """An exception class for reporting when a request that expected one
    and exactly one result got more than that.
    """
    exit_code = 5


class UsageError(TowerCLIError):
    """An exception class for reporting usage errors.

    This uses an exit code of 2 in order to match click (which matters more
    than following the erstwhile "standard" of using 64).
    """
    exit_code = 2
