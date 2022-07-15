#!/usr/bin/python3

import os
import sys
import time
import socket

# exit values
EXIT_SUCCESS=0
EXIT_FAILURE=1

try:
    import argparse
except:
    print ("Error, missing 'argparse'")
    sys.exit(EXIT_FAILURE)
try:
    import getpass
except:
    print ("Error, missing 'getpass'")
    sys.exit(EXIT_FAILURE)
try:
    import configparser
except:
    print ("Error, missing 'configparser'")
    sys.exit(EXIT_FAILURE)
try:
    import ipaddress
except:
    print ("Error, missing 'ipaddress', try: 'sudo pip install ipaddress'")
    sys.exit(EXIT_FAILURE)
try:
    import paramiko
except:
    print ("Error, missing 'paramiko', try: 'sudo pip install paramiko'")
    sys.exit(EXIT_FAILURE)

PACKAGE="Ias"
VERSION="0.4.1"
RELEASE_DATE="20220120"
AUTHOR="Saeed Bahmanabadi"
EMAIL="<bahmanabadi.s@gmail.com>"
URL="https://github.com/BlackCounter/Infra-as-service.git"


# max size for script #1MB
SCRIPT_MAXSIZE=1048576 

MODE_DRYRUN=False
MODE_QUIET=False
MODE_DEBUG=False

# supported protocols
PROTOCOL_SSH="ssh"
PROTOCOL_TELNET="telnet"

# default ssh connection timeout 5 seconds
CONNECTION_TIMEOUT=5

# defaults
PORT_SSH=22
PORT_TELNET=21

OUTPUT_SEPARATOR1="-----------------------------------------------------------------------------------------------------------------------"
OUTPUT_SEPARATOR2="#######################################################################################################################"
#OUTPUT_SEPARATOR='""""'
#OUTPUT_SEPARATOR=''

# elimina i warning deprecated
import warnings
warnings.filterwarnings(action='ignore',module='.*paramiko.*')


def _debugout(msg=""):
    global MODE_DEBUG
    if msg != "":
            if MODE_DEBUG:
                sys.stdout.write(PACKAGE + "(debug): " + msg+"\n")

def _txtout(msg="",quiet=False):
    if not quiet:
        sys.stdout.write(msg+"\n")

def _appout(host="", msg="",dryrun=False,quiet=False):
    str_dryrun=""
    if msg != "":
        if dryrun:
            str_dryrun=" (DRYRUN MODE)"
        if not quiet:
            sys.stdout.write(str(host)+str_dryrun+" -> "+msg +"\n")

def _exiterror(msg="",errno=1):
    _debugout ("_exiterror: errno " + str(errno))
    if msg != "":
        sys.stdout.write(PACKAGE + ": " + msg)
    sys.exit(errno)


def _pause(seconds=1):
    time.sleep(seconds)

class User:
    def __init__(self):
        self.username=None
        self.password=None
    
    def Set (self, username=None, password=None):
        if username != None:
            self.username=username
        if password != None:
            self.password=password

    def SetFromArgs (self, arg_username, arg_password):

        if arg_username != None:
            if arg_password != None:
                self.Set(arg_username,arg_password)
            else:
                self.Ask(ask_username=False, ask_password=True)
                self.Set(username=arg_username)
        else:
            self.Ask(ask_username=True, ask_password=True)


    def Ask(self, ask_username=True,ask_password=True):
        if ask_username:
            self.username=input("Username: ")
        if ask_password:
            self.password=getpass.getpass()

class Hosts:
    def __init__(self):
        self.hosts=[]

    def Validate(self,host):
        if host != None:
            try:
                ipaddress.ip_address(host)
            except:
                # passed host is not an ip address, let's consider it a "hostname"
                if len(str(host)) > 1:
                    return True

            return False

    def AddFromArgs(self, args):
        # process args
        self.hosts=args.split(",")

    def AddFromInventory(self, path=None, section="all_sections"):
        _debugout ("AddFromInventory: " + path + " " +section)
        # process (ini) inventory file
        inventory=configparser.ConfigParser(allow_no_value=True) # inventory file don't have a key value, just key for hostname/ip
        inventory.sections()
        
        if not os.path.isfile(path):
            _exiterror ("Error, cannot find inventory file '" + path+"'\nAborting.\n")

        try:
            inventory.read(path)
        except:
            _exiterror ("Error, cannot read inventory file '" + path+"'\nAborting.\n")
        
        # read all the hosts in all of the sections in the ini file
        secs=inventory.sections()
        for sec in secs:
            for key in inventory[sec]:
                if section == "all_sections":
                    self.hosts.append(str(key))
                else:
                    # add host only in in passed section name:
                    if section.lower() == sec.lower():
                        self.hosts.append(str(key))

    def AddFromInventoryAnsible(self, path=None, section="all_sections"):
        _debugout ("AddFromInventoryAnsible: " + path + " " +section)
        # process ansible like (ini) inventory file
        inventory=configparser.ConfigParser(allow_no_value=True) # inventory file don't have a key value, just key for hostname/ip
        inventory.sections()
        
        if not os.path.isfile(path):
            _exiterror ("Error, cannot find inventory file '" + path+"'\nAborting.\n")

        try:
            inventory.read(path)
        except:
            _exiterror ("Error, cannot read inventory file '" + path+"'\nAborting.\n")
        
        # read all the hosts in all of the sections in the ini file
        secs=inventory.sections()
        for sec in secs:
            # skip sections like [name:var]
            if sec.find(":") != -1:
                continue
            # skip commented sections
            if sec.find("#") == 0:
                continue

            for key in inventory[sec]:
                newstr=str(key)
                finalstr=""

                # skip commented
                if newstr.find("#") == 0:
                    continue

                # if there are spaces it splits the string
                # to consider only the first element
                if newstr.find(" ") != -1:
                    finalstr=newstr.split(" ")[0]
                else:
                    finalstr=newstr
                
                if section == "all_sections":
                    self.hosts.append(finalstr)

                else:
                    # add host only in in passed section name:
                    if section.lower() == sec.lower():
                        self.hosts.append(finalstr)


class Connection:
    
    def __init__ (self,protocol, port):

        self.protocol=protocol

        self.hostname=""
        self.port=port
        self.username=""
        self.password=""
        
        self.connection=None
        self.connected=False

        self.outoput=""
        self.error=""

        _debugout ("Connection (__init__):" + self.protocol)
        if self.protocol is PROTOCOL_SSH:
            self.connection=paramiko.client.SSHClient()
            self.connection.load_system_host_keys()
            self.connection.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

        elif self.protocol is PROTOCOL_TELNET:
            pass
        else:
            self.error="Error, no protocol given!"
            return None

    def Connect (self, hostname=None, port=None, username=None,password=None):

        self.hostname=hostname
        self.username=username
        self.password=password

        # clears output message and errors
        self.outoput=""
        self.error=""
        self.connected=False
        if port != None:
            self.port=int(port)

        if self.protocol is PROTOCOL_SSH:
            if self.ConnectSSH(self.hostname,self.port, self.username, self.password):
                return True

        elif self.protocol is PROTOCOL_TELNET:
            if self.ConnectTELNET(self.hostname,self.port, self.username, self.password):
                return True

        return False


    def ConnectSSH (self, hostname=None,port=None,username=None,password=None):

        self.hostname=hostname
        self.username=username
        self.password=password

        # clears output message and errors
        self.outoput=""
        self.error=""
        self.connected=False
        
        if port != None:
            self.port=int(port)    

        _debugout ("ConnectSSH:" + self.hostname +" " +str(self.port)+" "+self.username)
        try:
            self.connection.connect(self.hostname, self.port,self.username,self.password, timeout=CONNECTION_TIMEOUT )
        except socket.gaierror:
            self.error="Error (Connect), cannot resolve '" + self.hostname + "' !"
            return False
        except paramiko.BadHostKeyException:
            self.error="Error (Connect), bad host key exception!"
            return False
        except paramiko.AuthenticationException:
            self.error="Error (Connect), bad username or password!"
            return False
        except paramiko.SSHException:
            self.error="Error (Connect), general ssh exception!"
            return False
        except socket.error:
            self.error="Error (Connect), general socket error!"
            return False

        self.connected=True
        _debugout ("ConnectSSH: connected")
        return True


    def ConnectTELNET (self, hostname,port=None,username=None,password=None):
        self.hostname=hostname
        self.username=username
        self.password=password

        # clears output message and errors
        self.outoput=""
        self.error=""
        self.connected=False

        if port != None:
            self.port=int(port)    

        _debugout ("ConnectTELNET:" + self.hostname +" " +str(self.port)+" "+self.username)
        try:
            self.connection = telnetlib.Telnet(self.hostname)
        except:
            self.error="Error (ConnectTELNET), can't connect!"
            return False

        t.read_until(b"Username:")
        t.write(self.username.encode("ascii") + b"\n")
        if password:
            t.read_until(b"Password:")
            t.write(self.password.encode("ascii") + b"\n")

        self.connected=True
        return True

    def Exec (self, command):
        _debugout ("Exec: " + command)
        self.command=command

        if not self.connected:
            return 

        # clears output message and errors
        self.outoput=""
        self.error=""

        if self.protocol is PROTOCOL_SSH:
            try:
                stdin , stdout, stderr = self.connection.exec_command(command)
            except paramiko.SSHException:
                self.error="Error (Exec), general ssh exception!"
                return False
            self.output = stdout.read().decode('ascii').strip("\n")
            return True
            
        elif self.protocol is PROTOCOL_TELNET:
            self.connection.write(self.command+"\n")
            #tn.write("exit\n")
            self.output=connection.read_all()
            return True

        return False


    def ExecScript (self, path):
        _debugout ("ExecScript: " + path)
        self.script=path

        if not self.connected:
            return

        fsize=os.path.getsize(self.script)
        if (fsize > SCRIPT_MAXSIZE):
            self.error="Error, (ExecScript), file bigger than " + SCRIPT_MAXSIZE
            return False

        try:
            f = open(self.script, "r")
        except:
            self.error="Error (ExecScript) cannot read " + self.script
            return False

        flines=f.readlines()
        f.close()

        # clears output message and errors
        self.outoput=""
        self.error=""

        for line in flines:
            #skip empty lines
            if (line == "") or (line == None):
                continue
            # skip comments
            if line[0] == "#":
                continue

            _debugout ("command: " + line)

            if self.protocol is PROTOCOL_SSH:
                try:
                    stdin , stdout, stderr = self.connection.exec_command(line)
                except paramiko.SSHException:
                    self.error="Error (ExecScript), general ssh exception!"
                    return False
                self.output = stdout.read().decode('ascii').strip("\n")
                _txtout (self.output)
            
            elif self.protocol is PROTOCOL_TELNET:
                self.connection.write(self.command+"\n")
                #tn.write("exit\n")
                self.output=connection.read_all()
                _txtout (self.output)

        return True


    def Output (self):
        return str(self.output)

    def Error (self):
        return str(self.error)

    def Close(self):
        if not self.connected:
            return

        try:
            self.client.close()
        except:
            pass

def show_version():
    sys.stdout.write ("%s %s (%s) (%s)\n" %(PACKAGE,VERSION,RELEASE_DATE,URL))
    sys.stdout.write ("\n")
    sys.stdout.write ("Written by %s %s\n" %(AUTHOR,EMAIL))
    sys.exit(EXIT_SUCCESS)

def show_help():
    sys.stdout.write ("%s version %s Usage: %s [HOST or INVENTORY] [COMMAND or SCRIPT]\n" %(PACKAGE,VERSION,PACKAGE))
    sys.stdout.write ("\n")
    sys.stdout.write ("Required arguments:\n")
    sys.stdout.write ("      -H HOST       --hosts  HOSTS\n")
    sys.stdout.write ("                      hostname, ip or comma separated list of hosts\n")   
    sys.stdout.write ("      -I FILENAME,  --inventory FILENAME\n")
    sys.stdout.write ("                      inventory file with hosts list (supports Ansible inventory).\n")
    sys.stdout.write ("      -C COMMAND,   --command \"COMMAND\"\n")
    sys.stdout.write ("                      command to execute remotely between quotes\n")  
    sys.stdout.write ("      -S FILENAME,  --sctipt FILENAME\n")
    sys.stdout.write ("                      script file with commands to execute.\n")
    sys.stdout.write ("\n")
    sys.stdout.write ("Optional arguments:\n")
    sys.stdout.write ("      -U USERNAME,  --username USERNAME\n")
    sys.stdout.write ("                      username for the connection\n")
    sys.stdout.write ("      -P PASSWORD,  --password PASSWORD\n")
    sys.stdout.write ("                      password for the connection\n")
    sys.stdout.write ("      -p PORT,      --port PORT\n")
    sys.stdout.write ("                      port used for the connection, default 22\n")
    sys.stdout.write ("                    --protocol {ssh,telnet}\n")
    sys.stdout.write ("                      protocol to use valid values are ssh (default) or telnet\n")
    sys.stdout.write ("      -d,           --dryrun\n")
    sys.stdout.write ("                      only shows what will be done, doesn't execute commands\n")
    sys.stdout.write ("      -q,           --quiet\n")
    sys.stdout.write ("                      shows only essential output\n")
    sys.stdout.write ("      -v,           --version\n")
    sys.stdout.write ("                      output version information and exit\n")
    sys.stdout.write ("\n")
    sys.stdout.write ("Example: %s --hosts 192.168.0.10 --command \"uname\"\n" %(PACKAGE))
    sys.stdout.write ("Example: %s --inventory /home/users/inventory.ini --comand \"hostname\"\n" %(PACKAGE))
    sys.stdout.write ("Example: %s --hosts 102.168.0.10,192.168.0.20 --command \"uname && hostname\" --dryrun\n" %(PACKAGE))
    sys.stdout.write ("\n")    
    sys.stdout.write ("Report bugs on %s.\n" %(URL))
    sys.exit(EXIT_SUCCESS)
    

def main():
    """ """
    global MODE_DRYRUN, MODE_QUIET, MODE_DEBUG

    #argparser = argparse.ArgumentParser(prog=PACKAGE, add_help=False, usage='%(prog)s [options] BLAHBLHA OVerride thedefault')
    argparser = argparse.ArgumentParser(prog=PACKAGE, add_help=False)

    # this command are mutually exclusive for command or script file, and at least one must be specified
    exclusive_actions_group = argparser.add_mutually_exclusive_group(required=False)
    exclusive_actions_group.add_argument("-C","--command", help="command to execute remotely should quoted")
    exclusive_actions_group.add_argument("-S","--script", help="path to the script to execute")

    # this command are mutually exclusive for host list or inventory file, and at least one must be specified
    exclusive_inventory_group = argparser.add_mutually_exclusive_group(required=False)
    exclusive_inventory_group.add_argument("-H","--hosts", help="host or comma separated list of hosts")
    exclusive_inventory_group.add_argument("-I","--inventory", help="path to inventory file")

    # list of optional commands
    argparser.add_argument("-U","--username", help="username")
    argparser.add_argument("-P","--password", help="password")
    argparser.add_argument("-p","--port", help="port")
    argparser.add_argument("-t","--protocol", choices=['ssh', 'telnet'], default=PROTOCOL_SSH, help="protocol to use valid values are ssh (default)or telnet")
    # if specified dryrun is set to true
    argparser.add_argument("-d","--dryrun", help="only shows what will be done", action="store_true")
    # if specified quiet is set to true
    argparser.add_argument("-q","--quiet", help="shows only essential output", action="store_true")
    # if specified debug is set to true
    argparser.add_argument("-D","--debug", action="store_true", help=argparse.SUPPRESS) # not shown in normal help

    argparser.add_argument("-v","--version", help="output version information and exit", action='version',  version=str('%(prog)s ' + VERSION + " ("+RELEASE_DATE+")"))
    argparser.add_argument("-h","--help", help="display this help and exit", action='store_true')

    # parse args
    args=argparser.parse_args()

    # no argument given    
    if len(sys.argv)==1:
        sys.stderr.write(PACKAGE+": No arguments given.\n")
        sys.stderr.write("Try `"+PACKAGE+" --help' for more information.\n")
        sys.exit (EXIT_FAILURE)

    # no argument given    
    if (not args.command) and (not args.script):
        sys.stderr.write(PACKAGE+": No required option -C, --command or -S, --script given.\n")
        sys.stderr.write("Try `"+PACKAGE+" --help' for more information.\n")
        sys.exit (EXIT_FAILURE)

    # no argument given    
    if (not args.hosts) and (not args.inventory):
        sys.stderr.write(PACKAGE+": No required option -H, --hosts or -I, --inventory given.\n")
        sys.stderr.write("Try `"+PACKAGE+" --help' for more information.\n")
        sys.exit (EXIT_FAILURE)        
        
    if args.help:
        show_help()

    if args.dryrun:
        MODE_DRYRUN=True

    if args.quiet:
        MODE_QUIET=True

    if args.debug:
        MODE_DEBUG=True

    try:
        import signal
        # traps the sigint signal
        signal.signal(signal.SIGINT, signal_handler)
    except:
        pass

    # set username and password
    user=User()
    user.SetFromArgs(args.username, args.password)

    # add hosts to list
    if args.hosts != None:
        hosts=Hosts()
        hosts.AddFromArgs(args.hosts)

    elif args.inventory != None:
        hosts=Hosts()
        hosts.AddFromInventoryAnsible(path=args.inventory)

    port=PORT_SSH
    if args.port:
        try:
            port=int(args.port)
        except:
            _exiterror ("Error, port number should be an interger!\nAborting.\n")

    connection=Connection(args.protocol,int(port))

    counter=1
    if args.command != None:
        for host in hosts.hosts:
            _pause()
            _txtout("")
            if MODE_QUIET:
                _txtout(str(counter)+ ". ["+str(host)+":"+str(connection.port)+"] executing command: "+args.command)
            else:
                _txtout(str(counter)+ ". ["+str(host)+":"+str(connection.port)+"]")
                _appout (host,"Connect",MODE_DRYRUN, MODE_QUIET)
            connection.Connect(hostname=host, port=port, username=user.username,password=user.password)
            if not connection.connected:
                if MODE_DEBUG:
                    _debugout ("Can't connect. " + str(connection.error))
                else:
                    _appout (host,"Can't connect!",MODE_DRYRUN,False)
                
                counter=counter+1
                continue

            _appout (host,"Executing command: " + args.command,MODE_DRYRUN, MODE_QUIET)
            if connection.Exec(args.command):
                output = connection.Output()
                if output != "" and output != None:
                    _appout (host,"Getting output: ",MODE_DRYRUN,MODE_QUIET)
                    _txtout (OUTPUT_SEPARATOR1, MODE_QUIET)
                    _txtout (output)
                    _txtout (OUTPUT_SEPARATOR1 ,MODE_QUIET)

            connection.Close()
            _appout (host,"Connection closed.",MODE_DRYRUN,MODE_QUIET)
            counter=counter+1


    elif args.script != None:
        if not os.path.isfile(args.script):
            _exiterror ("Error, cannot find script file '" + args.script +"'\nAborting.\n")

        for host in hosts.hosts:
            _pause()
            _txtout("")
            if MODE_QUIET:
                _txtout(str(counter)+ ". ["+str(host)+":"+str(connection.port)+"] executing script: "+args.script)
            else:
                _txtout(str(counter)+ ". ["+str(host)+":"+str(connection.port)+"]")
                _appout (host,"Connect",MODE_DRYRUN, MODE_QUIET)

            connection.Connect(hostname=host, port=port, username=user.username,password=user.password)
            if not connection.connected:
                if MODE_DEBUG:
                    _debugout ("Can't connect. " + str(connection.error))
                else:
                    _appout (host,"Can't connect!",MODE_DRYRUN,False)
                
                counter=counter+1
                continue

            _appout (host,"Executing script: " + args.script,MODE_DRYRUN, MODE_QUIET)
            _appout (host,"Getting output: ",MODE_DRYRUN,MODE_QUIET)
            _txtout (OUTPUT_SEPARATOR1, MODE_QUIET)
            if not connection.ExecScript(args.script):
                _exiterror ("Error, '" + connection.error + "'")
            _txtout (OUTPUT_SEPARATOR1 ,MODE_QUIET)
            connection.Close()
            _appout (host,"Connection closed.",MODE_DRYRUN,MODE_QUIET)
            counter=counter+1


if __name__ == "__main__":
    main()
    sys.exit(EXIT_SUCCESS)


