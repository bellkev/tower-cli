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

from tower_cli import models
from tower_cli.utils import exceptions as exc


class Resource(models.Resource):
    cli_help = 'Manage credentials within Ansible Tower.'
    endpoint = '/credentials/'

    name = models.Field(unique=True)
    description = models.Field(required=False)

    # Who owns this credential?
    owner = models.ImplicitField()
    user = models.Field(type=int, required=False)
    team = models.Field(type=int, required=False)

    # What type of credential is this (machine, SCM, etc.)?
    kind = models.Field(
        choices=('ssh', 'scm', 'aws', 'rax'),
        default='ssh',
        help_text='The type of credential being added. '
                  'Valid options are: ssh, scm, aws, rax.',
        show_default=True,
    )

    # SSH and SCM fields.
    username = models.Field(required=False)
    password = models.Field(password=True, required=False)
    private_key = models.Field(type=models.File('r'), required=False)
    private_key_password = models.Field(password=True, required=False)

    # SSH specific fields.
    sudo_username = models.Field(required=False)
    sudo_password = models.Field(password=True, required=False)
    vault_password = models.Field(password=True, required=False)

    # AWS fields.
    access_key = models.Field(required=False)
    secret_key = models.Field(required=False)

    # Rackspace fields.
    api_key = models.Field(required=False)

    @owner.formula
    def determine_owner(self, data):
        """Determine the owner value based on whether user or team have
        been set.
        """
        # Sanity check: If both user and team are meaningfully set, then
        # this is a validation error.
        if data.get('user', None) and data.get('team', None):
            raise exc.ValidationError('A credential may not be owned by both '
                                      'a user and a team.')

        # Return the owner value corresponding to the user or team key that
        # is set, or None if neither is set.
        if data.get('user', None):
            return 'user'
        if data.get('team', None):
            return 'team'
        return None
