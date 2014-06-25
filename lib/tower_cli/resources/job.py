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
from copy import copy
from datetime import datetime
from getpass import getpass

import click

from tower_cli import models, get_resource
from tower_cli.api import client
from tower_cli.resources import cli_command


class Resource(models.BaseResource):
    """A resource for jobs.

    As a base resource, this resource does *not* have the normal create, list,
    etc. methods.
    """
    cli_help = 'Launch or monitor jobs.'
    endpoint = '/jobs/'

    @cli_command
    @click.option('--job-template', type=int)
    def launch(self, job_template):
        """Launch a new job based on a job template.

        Creates a new job in Ansible Tower, immediately stats it, and
        returns back an ID in order for its status to be monitored.
        """
        # Get the job template from Ansible Tower.
        # This is used as the baseline for starting the job.
        jt_resource = get_resource('job_template')
        jt = jt_resource.get(job_template)

        # Update the job data by adding an automatically-generated job name,
        # and removing the ID.
        data = copy(jt)
        data.pop('id')
        data['name'] = 'CLI Job Invocation: %s' % datetime.now()

        # Create the new job in Ansible Tower.
        job = client.post('/jobs/', data=data)

        # There's a non-trivial chance that we are going to need some
        # additional information to start the job; in particular, many jobs
        # rely on passwords entered at run-time.
        #
        # If there are any such passwords on this job, ask for them now.
        job_start_info = client.get('/jobs/%d/start/' % job['id'])
        start_data = {}
        for password in job_start_info.get('passwords_needed_to_start', []):
            start_data[password] = getpass('Password for %s: ' % password)

        # Actually start the job.
        result = client.post('/jobs/%d/start/' % job['id'], start_data)
        return result
