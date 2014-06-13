
# Copyright 2013, AnsibleWorks Inc.
# Michael DeHaan <michael@ansibleworks.com>
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

import datetime
import exceptions
import optparse
import os
import getpass
import json
import urllib2
import ConfigParser

class BaseException(exceptions.Exception):
    def __init__(self, msg):
        super(BaseException, self).__init__()
        self.msg = msg

    def __str__(self):
        return "ERROR: %s" % self.msg

class CommandNotFound(BaseException):
    pass

class SortedOptParser(optparse.OptionParser):

    def format_help(self, formatter=None):
        self.option_list.sort(key=operator.methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)

def get_parser():

    usage = "%prog [options]"
    parser = SortedOptParser(usage)

    parser.add_option('-u', '--username', dest='username', default=None, type='str')
    parser.add_option('-p', '--password', dest='password', default=None, type='str')
    parser.add_option('-s', '--server',   dest='server',   default=None, type='str')
  
    return parser

class Connection(object):

    def __init__(self, server):
        self.server = server

    def get(self, endpoint):
        url = "%s%s" % (self.server, endpoint)
        data = None
        try:
            response = urllib2.urlopen(url)
            data = response.read()
        except Exception, e:
            raise BaseException(str(e) + ", url: %s" % (url))
        result = json.loads(data)
        return result

    def post(self, endpoint, data):
        url = "%s%s" % (self.server, endpoint)
        request = urllib2.Request(
            url, 
            json.dumps(data),
            {'Content-type': 'application/json'}
        )
        data = None
        try:
            response = urllib2.urlopen(request)
            data = response.read()
        except Exception, e:
            raise BaseException("%s, url: %s, data: %s, response: %s" % (str(e), url, data, e.read()))
        try:
            result = json.loads(data)
            return result
        except:
            return data

def get_config_parser():
    parser = ConfigParser.ConfigParser()
    path1 = os.path.expanduser(os.environ.get('AWX_CLI_CONFIG', "~/.tower_cli.cfg"))
    path2 = "/etc/awx/tower_cli.cfg"

    if os.path.exists(path1):
        parser.read(path1)
    elif os.path.exists(path2):
        parser.read(path2)
    else:
        return None
    return parser

def get_config_value(p, section, key, default):
    try:
        return p.get(section, key)
    except:
        return default

def get_config_default(p, key, defaults, section='general'):
    return get_config_value(p, section, key, defaults[key])


def dump(data=None, **kwargs):
    """Dump the given data to a string."""
    data = data or {}
    data.update(kwargs)
    return json.dumps(data, indent=4, sort_keys=True)
