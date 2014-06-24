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

        return
        ########
                # get the parameters needed to start the job (if any)
        # prompt for values unless given on command line (FIXME)

        print "URL=%s" % jt_jobs_url

        job_id = job_result['id']
        job_start_url = "/api/v1/jobs/%d/start/" % job_id
        job_start_info = handle.get(job_start_url)
        start_data = {}
        for password in job_start_info.get('passwords_needed_to_start', []):
            value = getpass.getpass('%s: ' % password)
            start_data[password] = value

        # start the job 
        job_start_result = handle.post(job_start_url, start_data)
        print common.dump(job_start_result) 
