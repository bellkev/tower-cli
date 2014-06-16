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

from click import echo, secho


def echo_json(obj, indent=2, sort_keys=False, **kwargs):
    """Echo a JSON object using `click.echo`."""
    return echo(json.dumps(obj, indent=indent, sort_keys=False), **kwargs)


def secho_json(obj, indent=2, sort_keys=False, **kwargs):
    """Echo a JSON object using `click.secho`."""
    return secho(json.dumps(obj, indent=indent, sort_keys=False), **kwargs)
