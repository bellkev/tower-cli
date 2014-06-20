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
from tower_cli.utils.types import File


class Resource(models.Resource):
    cli_help = 'Manage credentials within Ansible Tower.'
    endpoint = '/credentials/'

    name = models.Field(unique=True)
    description = models.Field(required=False)

    # FIXME: Make the one of these provided cause "owner" to be set
    #        correctly.
    user = models.Field(type=int)
    team = models.Field(type=int, required=False)

    type = models.Field(default='machine')

    # SSH and SCM fields.
    username = models.Field(required=False)
    password = models.Field(password=True, required=False)
    private_key = models.Field(type=File('r'), required=False)
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
