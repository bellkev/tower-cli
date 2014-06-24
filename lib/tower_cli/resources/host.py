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
    cli_help = 'Manage hosts belonging to a group within an inventory.'
    endpoint = '/hosts/'

    name = models.Field(unique=True)
    description = models.Field(required=False)
    group = models.Field(type=int)
    enabled = models.Field(type=bool, default=True, show_default=True)
    variables = models.Field(type=models.File('r'), required=False)