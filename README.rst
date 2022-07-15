
Ias
=====


A simple and quick program to execute and automate remote commands.
-------------------------------------------------------------------

Ias.py is a Python script to easily and quickly run a command or multiple commands on remote and local 
hosts and devices via ssh (telnet is also supported). It is also able to automate repetitive tasks on 
many hosts using inventory files from Ansible, or simple .ini inventory files.

rduty is currently tested on Python3, it hasn't been tested yet on other
Python versions.


Installation
------------
Python3 is needed, other than that, the rduty package is installation is very simple, but there are
some  dependencies which you might have to install as well:

.. code-block:: console

   $ sudo pip install paramiko
  
.. code-block:: console

   $ make install

By default rduty will be installed with the '/usr/local' prefix. You can 
change this by passing 'PREFIX=the_prefix' to make:

.. code-block:: console

   $ make PREFIX=/usr install

When rduty is executed it will check for the needed dependencies and report
if anything is missing.


Usage
-----

**Usage:** `rduty [HOST or INVENTORY] [COMMAND or SCRIPT] ...`

Some usage examples:

.. code-block:: sh

  $ Ias -H 192.168.0.10 -C "ls" 
  
.. code-block:: sh

   $ Ias -H 192.168.0.10,192.168.0.20,server.mydomain.local -C "uname -a" 

.. code-block:: sh

   $ Ias -I myinventory/servers.ini --script "/home/user/commands_list.txt" 

.. code-block:: sh

   $ Ias -I myinventory/servers.ini --script "/home/user/commands_list.txt" --dryrun


**Options:**

.. csv-table::
   :header: Option, Description
   :widths: 30, 70

   "Required arguments:",""
   "``-H``, ``--hosts host1,host2,...``","A hostname or IP, or a comma separated list of hosts"
   "``-I``, ``--inventory FILENAME``","path to inventory file (.ini or Ansible format)"
   "``-C``, ``--command COMMAND``","remote command to ececute on the remote hosts or devies"
   "``-S``, ``--script FILENAME``","path to a list of commands to ececute on the remote hosts or devies"
   "Optional arguments:",""
   "``-U``, ``--username USERNAME``","username for the remote connection"
   "``-P``, ``--password PASSWORD``","password for the remote connection"
   "``-p``, ``--port PORT``","port used for the connection, default is 22"
   "``-d``, ``--dryrun``","doesn't execute any command on the hosts"
   "``-q``, ``--quiet``","shows essential output only"
   "``-v``, ``--version``",output version information and exit.
   "``-h``, ``--help``",show this help and exit.


Script file and Inventory file format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A script is a file with a list of command to execute on the remote host, each one on a new line:

.. code-block:: sh

   uname -a
   df
   hostname

A Inventory file is a .ini file with a list of hosts with the folling format:

In your ~/.ssh/config file you can add this lines for example:
.. code-block:: ini

   Host sever1.localdomain.local
   HostName 192.26.32.32
   Port 2200

   Host server2.localdomain.local
   HostName 192.26.32.32
   Port 8888

Then use these aliases in your Ansible inventory:
.. code-block:: ini

   [servers]
   server1.localdomain.local
   server2.localdomain.local
   [dbs]
   db1.localdomain.local


Command line
~~~~~~~~~~~~

**Usage:** `Ias [HOST or INVENTORY] [COMMAND or SCRIPT] ...`

.. code-block:: sh

   $ ./Ias.py  -H 192.168.0.3 -C "uname" -p 22
   Username: test
   Password: 
   1. [192.168.0.3:22]
   192.168.0.3 -> Connect
   192.168.0.3 -> Executing command: uname
   192.168.0.3 -> Getting output: 
   -----------------------------------------------------------------------------------------------------------------------
   Linux
   -----------------------------------------------------------------------------------------------------------------------
   192.168.0.3 -> Connection closed.


Contact
-------

The latest version of Ias is available on GitHub https://github.com/BlackCounter/Infra-as-service .
For questions, bug reports, suggestions, etc. please contact the author.

License
-------

This software is licensed under the GNU GPL2.

© 2022 Saeed Bahmanabadi.
