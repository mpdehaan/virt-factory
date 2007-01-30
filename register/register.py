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
    
    def register(self):
        # should return a machine_id, maybe more
        print "self.token", self.token
        rc = self.server.register_new_machine(self.token)

        print rc

        return rc

    # for a machine that has an id (either from the wui, or as part of the
    # generated kickstart, assosicate it with a hostname and ip_addr so that
    # taskotron can contact its node api
    def associate(self, machine_id, hostname, ip_addr, mac_addr):
        # FIXME: hostname is not being used.
        rc = self.server.register_associate_machine(self.token, machine_id, ip_addr, mac_addr)
        return rc


def showHelp():
    print "register [--help] [--token] [--serverurl=]"


def main(argv):

    regtoken   = None
    username   = None
    password   = None
    server_url = None
    provision  = False

    try:
        opts, args = getopt.getopt(argv[1:], "hPt:u:p:s:", [
            "help", 
            "provision"
            "token=", 
            "username=",
            "password=", 
            "serverurl="
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
        if opt in ["-P", "--provision"]:
            provision = True
        if opt in ["-t", "--token"]:
            regtoken = val
        if opt in ["-u", "--username"]:
            username = val
        if opt in ["-p", "--password"]:
            password = val
        if opt in ["-s", "--serverurl"]:
            server_url = val

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

    
    rc = reg_obj.register()

    if rc[0] != 0:
        print "There was an error logging in"
        # FIXME: why don't we just return an xmlrpc fault here?
        sys.exit(2)
        
    machine_id = rc[1]['data']
        
    net_info = machine_info.get_netinfo(server_url)
    # FIXME: error checking on this value...
    # FIXME: fill in hardware info.
    print reg_obj.associate(machine_id, net_info['hostname'], net_info['ipaddr'], net_info['hwaddr'])

    if provision:
        # now invoke koan pointed at the server.
        if not os.path.exists("/usr/bin/koan"):
            print "Cannot provision.  Missing /usr/bin/koan"
            sys.exit(1)
        else:
            # FIXME: fill in with magic from the database.
            rc = subprocess.call["/usr/bin/koan","--replace-self", "--profile=FIXME" % profile,"--server=FIXME" % server]
            if rc != 0:
                print "provisioning failed."
                sys.exit(1)
            else:
                print "provisioning succeeded.  Reboot?"
    else:
        print "done."

if __name__ == "__main__":
    main(sys.argv)


