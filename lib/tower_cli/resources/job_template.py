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


class Resource(models.Resource):
    cli_help = 'Manage job templates.'
    endpoint = '/job_templates/'

    name = models.Field(unique=True)
    description = models.Field(required=False)
    job_type = models.Field(
        choices=('run', 'check'),
        default='run',
        show_default=True,
    )
    inventory = models.Field(type=int)
    project = models.Field(type=int)
    playbook = models.Field()
    machine_credential = models.Field(type=int)
    cloud_credential = models.Field(type=int)
    forks = models.Field(type=int, default=0, show_default=True)
    limit = models.Field(required=False)
    verbosity = models.Field(
        choices=('default', 'verbose', 'debug'),
        default='default',
        show_default=True,
    )  # Perhaps do this with a -v flag?
    job_tags = models.Field(required=False)
    variables = models.Field(type=models.File('r'), required=False)
