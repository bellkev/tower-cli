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

from click.decorators import _param_memo as add_param


def use_parameters(source_command, exclude=()):
    """Copy the parameters from one `click` command function to another.

    This command iterates over each member of the `params` list on the source
    function and appends it to the destination function.
    """
    def decorator(dest_command):
        for param in source_command.params[::-1]:
            if param.name not in exclude:
                add_param(dest_command, param)
        return dest_command
    return decorator
