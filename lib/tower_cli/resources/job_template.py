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

from tower_cli import models, get_resource
from tower_cli.resources import cli_command
from tower_cli.utils.types import MappedChoice


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
    machine_credential = models.Field('credential', type=int)
    cloud_credential = models.Field(type=int, required=False)
    forks = models.Field(type=int, default=0, show_default=True)
    limit = models.Field(required=False)
    verbosity = models.Field(
        default='default',
        show_default=True,
        type=MappedChoice([(0, 'default'), (1, 'verbose'), (2, 'debug')]),
    )
    job_tags = models.Field(required=False)
    variables = models.Field(type=models.File('r'), required=False)

    @cli_command(no_args_is_help=True, use_fields_as_options=False)
    @click.argument('job_template_id')
    def launch(self, job_template_id):
        """Launch a job based on this job template.

        This is a mapping to `job launch`, such that:
            - tower job_template launch 42
            - tower job launch --template 42
        ...are equivalent.
        """
        job_resource = get_resource('job')
        return job_resource.launch(job_template=job_template_id)

        return {}
        # add some more info needed to start the job
        # NOTE: a URL to launch job templates directly
        # may be added later, but this is basically a copy of the job template
        # data to the jobs resource, which is also fine.

        now = str(datetime.datetime.now())
        data.update(dict(
            name = 'cli job invocation started at %s' % now,
            verbosity = 0,
        ))

        # post a new job

        jt_jobs_url = "%sjobs/" % jt_url
        job_result = handle.post(jt_jobs_url, data)

        # get the parameters needed to start the job (if any)
        # prompt for values unless given on command line (FIXME)

        print("URL=%s" % jt_jobs_url)

        job_id = job_result['id']
        job_start_url = "/api/v1/jobs/%d/start/" % job_id
        job_start_info = handle.get(job_start_url)
        start_data = {}
        for password in job_start_info.get('passwords_needed_to_start', []):
            value = getpass.getpass('%s: ' % password)
            start_data[password] = value

        # start the job 
        job_start_result = handle.post(job_start_url, start_data)
        print (common.dump(job_start_result) )

        # TODO: optional status polling (FIXME)

