#!/usr/bin/python

"""
ShadowManager client code.

Copyright 2007, Red Hat, Inc
Adrian Likins <alikins@redhat.com>
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import machine_info

import getopt
import sys
import xmlrpclib
import socket
import os
import os.path

ERR_TOKEN_INVALID = 2   # from codes.py, which we don't import because it's not installed ??
ERR_ARGUMENTS_INVALID = 8 # ...

class Server(xmlrpclib.ServerProxy):
    def __init__(self, url=None):
        xmlrpclib.ServerProxy.__init__(self, url)



class Register(object):
    def __init__(self,url):
        self.server = Server(url)
        self.token = None

    # assume username/password exist, so no user creation race conditions to avoid
    # like RHN
    def login(self, username, password):
        if not self.token:
            self.token = self.server.user_login(username, password)[1]['data']
    
    def register(self, hostname, ip, mac, profile_name, virtual):
        # should return a machine_id, maybe more
        print "--------------------"
        print "Registering..."
        print "  token=", self.token
        print "  hostname=", hostname,
        print "  ip=", ip
        print "  mac=", mac
        print "  profile_name=", profile_name
        print "  virtual=", virtual
        print "---------------------"
        if profile_name is None:
            profile_name = ""
        if mac is None:
            mac = "00:00:00:00:00:00"
        try:
            rc = self.server.register(self.token, hostname, ip, mac, profile_name, virtual)
        except TypeError:
            print "must specify --profilename"
            sys.exit(1)
        if rc[0] == 0:
            print "Registration succeeded."
            fd1 = open("/etc/sysconfig/virtfactory/token","w+")
            fd1.write(self.token)
            fd1.close()
            fd2 = open("/etc/sysconfig/virtfactory/server","w+")
            fd2.write(hostname)
            fd2.close()
            fd3 = open("/etc/sysconfig/virtfactory/mac", "w+")
            fd3.write(mac)
            fd3.close()
            fd4 = open("/etc/sysconfig/virtfactory/profile", "w+")
            fd4.write(profile_name)
            fd4.close()
        else:
            print "Failed: ", rc
        return rc


def showHelp():
    print "register [--help] [--token] [--serverurl=]"


def main(argv):

    regtoken   = "UNSET"
    username   = None
    password   = None
    server_url = None
    profile_name = ""
    virtual      = False

    # ensure we have somewhere to save parameters to, the node daemon will want
    # to know them later.

    if not os.path.exists("/etc/sysconfig/virtfactory"):
        os.makedirs("/etc/sysconfig/virtfactory")

    try:
        opts, args = getopt.getopt(argv[1:], "ht:u:p:s:P:v", [
            "help", 
            "token=", 
            "username=",
            "password=", 
            "serverurl=",
            "profilename=",
            "virtual"
        ])
    except getopt.error, e:
        print "Error parsing command list arguments: %s" % e
        showHelp()
        sys.exit(1)

    for (opt, val) in opts:
        print "DEBUG: this (%s,%s)" % (opt,val)
        if opt in ["-h", "--help"]:
            showHelp()
            sys.exit(1)
        if opt in ["-t", "--token"]:
            regtoken = val
        if opt in ["-u", "--username"]:
            username = val
        if opt in ["-p", "--password"]:
            password = val
        if opt in ["-s", "--serverurl"]:
            server_url = val
        if opt in ["-i", "--profilename"]:
            print "read the profile name"
        if opt in ["-v", "--virtual"]:
            virtual = True
            profile_name = val

    if server_url is None:
        print "must specify --serverurl, ex: http://foo.example.com:5150"
        sys.exit(1)
    
    if regtoken is None:
        if username is None:
           print "must specify --token or --username and --password"
           sys.exit(1)
        elif password is None:
           print "must specify --password"
           sys.exit(1)        

    reg_obj = Register(server_url)
    if regtoken:
        reg_obj.token = regtoken
    else:
        reg_obj.login(username, password)

    net_info = machine_info.get_netinfo(server_url)
    
    try:
        rc = reg_obj.register(net_info['hostname'], net_info['ipaddr'], net_info['hwaddr'], profile_name, virtual)
    except socket.error:
        print "Could not connect to server."
        sys.exit(1)
    if rc[0] == ERR_TOKEN_INVALID:
        print "Bad token!  No registration for you!"
        sys.exit(rc[0])
    elif rc[0] == ERR_ARGUMENTS_INVALID:
        print "Invalid arguments.  Possibly missing --profilename ?"
        sys.exit(rc[0])
    elif rc[0] != 0:
        print "There was an error.  Check the server side logs."
        sys.exit(rc[0])

if __name__ == "__main__":
    main(sys.argv)



