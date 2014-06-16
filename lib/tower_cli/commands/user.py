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

import json

import click

from tower_cli.api import client
from tower_cli.utils import exceptions as exc
from tower_cli.utils.echo import echo_json
from tower_cli.utils.decorators import use_parameters


@click.group()
def user():
    """Manage users within Ansible Tower."""


@user.command()
@click.option('--username', help='Match against the provided username.')
@click.option('--email', help='Match against the provided e-mail address.')
@click.option('--first-name', help='Match against the provided first name.')
@click.option('--last-name', help='Match against the provided last name.')
@click.option('--is-superuser', type=bool, default=None,
              help='Match against superusers if set to true, or '
                   'non-superusers if set to False.')
def list(**kwargs):
    """List users in Ansible Tower.

    Optionally filter this list by use of command-line flags and
    arguments.

    If no users match the provided arguments, returns a message to this
    effect, but it's not considered an error. Use the `get` command to
    expect one and exactly one match.
    """
    results = client.get('/users/', params=kwargs).json()['results']
    echo_json(results)


@user.command()
@click.argument('user_id', nargs=1, required=False, type=int)
@use_parameters(list)
def get(user_id=None, **kwargs):
    """Get a single user in Ansible Tower.

    If the user is not found, send back a non-zero exit status and an
    error.
    """
    # Sanity check: If no user is provided and no keyword arguments are
    # provided, then this is an error.
    if not user_id and not any(kwargs.values()):
        raise exc.UsageError('Must provide either a user ID as an argument '
                             'or filter flags to identify a user.')

    # Attempt to get the user from Tower.
    if user_id:
        kwargs['id'] = user_id
    response = client.get_one('/users/', params=kwargs).json()

    # Echo the result.
    echo_json(response['results'][0])


@user.command()
@click.argument('user_id', type=int)
@use_parameters(list)
def modify(user_id, **kwargs):
    """Modify the given user, setting the given values.
    Return the user object on success.
    """
    # Strip out None values from kwargs.
    kwargs = dict([(k, v) for k, v in kwargs.items() if v is not None])

    # Make the request.
    response = client.patch('/users/%d/' % user_id, data=kwargs)
    echo_json(response.json())


@user.command()
@click.argument('user_id', type=int)
def remove(user_id):
    """Remove the given user entirely."""
    response = client.delete('/users/%d/' % user_id)
    echo_json(response.json())
