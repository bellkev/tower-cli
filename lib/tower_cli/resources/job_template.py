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

import click

from tower_cli import models
from tower_cli.resources import cli_command


class Resource(models.Resource):
    cli_help = 'Manage job templates.'
    endpoint = '/job_templates/'

    name = models.Field(unique=True)
    description = models.Field(required=False)
    job_type = models.Field(
        default='run',
        show_default=True,
        type=click.Choice(['run', 'check']),
    )
    inventory = models.Field(type=int)
    project = models.Field(type=int)
    playbook = models.Field()
    machine_credential = models.Field(type=int)
    cloud_credential = models.Field(type=int)
    forks = models.Field(type=int, default=0, show_default=True)
    limit = models.Field(required=False)
    verbosity = models.Field(
        default='default',
        show_default=True,
        type=click.Choice(['default', 'verbose', 'debug']),
    )
    job_tags = models.Field(required=False)
    variables = models.Field(type=models.File('r'), required=False)

    @cli_command(no_args_is_help=True, use_fields_as_options=False)
    @click.argument('job_template_id')
    def launch(self, job_template_id):
        """Launch a job based on this job template."""
        return {}
