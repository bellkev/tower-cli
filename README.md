## Welcome to tower-cli

**tower-cli** is a command line tool for Ansible Tower. It allows Tower
commands to be easily run from the Unix command-line.


### About Tower

Tower is a GUI and REST interface for Ansible that supercharges it by adding
RBAC, centralized logging, autoscaling/provisioning callbacks, graphical
inventory editing, and more.

See http://ansible.com/tower for more details.  

Tower is free to use for up to 10 nodes, and you can purchase a license for
more at http://ansible.com/ansible-pricing.


### Capabilities

You can use this command line tool to send commands to the Tower API.

For instance, you might use this tool with Jenkins, cron, or in-house
software to trigger remote execution of Ansible playbook runs.


### Installation

Install _tower-cli_ using pip:

```bash
$ pip install tower-cli
```


### Configuration

Configuration can be set in several places, and follows the following
precedence, from least to greatest:

  * internal defaults
  * `/etc/awx/tower_cli.cfg`
  * `~/.tower_cli.cfg`
  * command line paramaters

A configuration file is a simple file with keys and values, separated by
`:` or `=`:

```ini
host: tower.example.com
username: admin
password: p4ssw0rd
```

### Usage

CLI invocation looks like this:

```
# list subcommands
tower-cli --help

# run a command (no config file)
tower-cli version --username admin --password password --server tower.example.com

# run a command (config file)
tower-cli version
```

Here is an example of launching a job template to run an Ansible playbook.

As a note, the system will prompt for any parameters set to `ASK` in Tower,
so be sure all of this information is filled in if you are using this from a
system like Jenkins or cron.  All we need to specify is the template ID.

```
tower-cli job launch --template 5
```

### License

While Tower is commercial software, _tower-cli_ is an open source project,
and we encorage contributions.  Specfically, this CLI project is licensed
under the Apache license.

Michael DeHaan
(C) 2014, Ansible, Inc.
