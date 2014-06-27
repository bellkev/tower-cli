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

from tower_cli import models
from tower_cli.utils import exceptions as exc
from tower_cli.utils import types


class Resource(models.Resource):
    cli_help = 'Manage credentials within Ansible Tower.'
    endpoint = '/credentials/'

    name = models.Field(unique=True)
    description = models.Field(required=False)

    # Who owns this credential?
    user = models.Field(
        type=types.Related('user', criterion='username'),
        required=False,
    )
    team = models.Field(
        type=types.Related('team'),
        required=False,
    )

    # What type of credential is this (machine, SCM, etc.)?
    kind = models.Field(
        help_text='The type of credential being added. '
                  'Valid options are: ssh, scm, aws, rax.',
        type=click.Choice(['ssh', 'scm', 'aws', 'rax']),
    )

    # SSH and SCM fields.
    username = models.Field(required=False)
    password = models.Field(password=True, required=False)
    private_key = models.Field('ssh_key_data',
        help_text="The full path to the SSH private key to store. "
                  "(Don\'t worry; it's encrypted.)",
        required=False,
        type=models.File('r'),
    )
    private_key_password = models.Field('ssh_key_unlock', password=True,
                                                          required=False)

    # SSH specific fields.
    sudo_username = models.Field(required=False)
    sudo_password = models.Field(password=True, required=False)
    vault_password = models.Field(password=True, required=False)

    # AWS fields.
    access_key = models.Field(required=False)
    secret_key = models.Field(required=False)

    # Rackspace fields.
    api_key = models.Field(required=False)
