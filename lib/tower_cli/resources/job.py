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
import sys
import time

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
        job = client.post('/jobs/', data=data).json()

        # There's a non-trivial chance that we are going to need some
        # additional information to start the job; in particular, many jobs
        # rely on passwords entered at run-time.
        #
        # If there are any such passwords on this job, ask for them now.
        job_start_info = client.get('/jobs/%d/start/' % job['id']).json()
        start_data = {}
        for password in job_start_info.get('passwords_needed_to_start', []):
            start_data[password] = getpass('Password for %s: ' % password)

        # Actually start the job.
        result = client.post('/jobs/%d/start/' % job['id'], start_data)
        return {
            'changed': True,
            'id': job['id'],
        }

    @cli_command(no_args_is_help=True)
    @click.option('--min-interval',
                  default=1, help='The minimum interval to request an update '
                                  'from Tower.')
    @click.option('--max-interval',
                  default=30, help='The maximum interval to request an update '
                                   'from Tower.')
    def monitor(self, pk, min_interval=1, max_interval=30, outfile=sys.stdout):
        """Monitor a running job.

        Blocks further input until the job completes (whether successfully or
        unsuccessfully) and a final status can be given.
        """
        SPINNER_CHARS = ('|', '/', '-', '\\')
        longest_string = 0
        interval = min_interval

        # Poll the Ansible Tower instance for status, and print the status
        # to the outfile (usually standard out).
        #
        # Note that this is one of the few places where we use `click.secho`
        # even though we're in a function that might theoretically be imported
        # and run in Python.  This seems fine; outfile can be set to /dev/null
        # and very much the normal use for this method should be CLI
        # monitoring.
        job = self.status(pk)
        while job['status'] != 'successful':
            # If the job has failed, we want to raise an Exception for that
            # so we get a non-zero response.
            if job['failed']:
                click.secho('\r' + ' ' * longest_string + '\n', file=outfile)
                raise exc.JobFailure('Job failed.')

            # Print the current status.
            output = '\rCurrent status: %s' % job['status']
            if longest_string > len(output):
                output += ' ' * (longest_string - len(output))
            else:
                longest_string = len(output)
            click.secho(output, nl=False, file=outfile)

            # Increment the interval and put the processor to sleep
            # briefly.
            interval = min(interval * 1.5, max_interval)
            time.sleep(interval)

            # Ask the server for a new status.
            job = self.status(pk)

            # Wipe out the previous output
            click.secho('\r' + ' ' * longest_string, file=outfile)

        # Done; return the result
        return job

    @cli_command(no_args_is_help=True)
    @click.option('-v', '--verbose', is_flag=True, default=False,
                                     help='Print more detail.')
    def status(self, pk, verbose=False):
        """Print the current job status."""
        # Get the job from Ansible Tower.
        job = client.get('/jobs/%d/' % pk).json()

        # In most cases, we probably only want to know the status of the job
        # and the amount of time elapsed. However, if we were asked for
        # verbose information, provide it.
        if verbose:
            return job

        # Print just the information we need.
        return {
            'elapsed': job['elapsed'],
            'failed': job['failed'],
            'status': job['status'],
        }
