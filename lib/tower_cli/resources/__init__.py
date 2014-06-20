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

def cli_command(method=None, **kwargs):
    """Mark this method as a CLI command.
    
    This will only have any meaningful effect in methods that are members of a
    Resource subclass.
    """
    if not method or kwargs:
        def decorator(method):
            method._cli_command = True
            method._cli_command_attrs = kwargs
            return method
        return decorator
    else:
        method._cli_command = True
        return method
