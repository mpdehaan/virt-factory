#!/usr/bin/python

"""
ShadowManager client code.

Copyright 2007, Red Hat, Inc
Adrian Likins <alikins@redhat.com>

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



class Server(xmlrpclib.ServerProxy):
    def __init__(self, url=None):
        xmlrpclib.ServerProxy.__init__(self, url)



class Register(object):
    def __init__(self):
        self.server = Server("http://127.0.0.1:5150")
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
        rc = self.server.register_associate_machine(self.token, machine_id, ip_addr, mac_addr)

        return rc


def showHelp():
    print "register [--help] [--regtoken]"


def main(argv):

    regtoken = None
    try:
        opts, args = getopt.getopt(argv[1:], "h", ["help", "regtoken="])
    except getopt.error, e:
        print "Error parsing command list arguments: %s" % e
        showHelp()
        sys.exit(1)

    for (opt, val) in opts:
        if opt in ["-h", "--help"]:
            showHelp()
            sys.exit(1)
        if opt in ["--regtoken"]:
            regtoken = val
        
    reg_obj = Register()
    print "regtoken", regtoken
    if regtoken:
        reg_obj.token = regtoken
    else:
        reg_obj.login("admin", "fedora")

    
    rc = reg_obj.register()

    if rc[0] != '0':
        print "There was an error logging in"
        # FIXME: why don't we just return an xmlrpc fault here?
        sys.exit(2)
        
    machine_id = rc[1]['data']
        
    server_url = "http://127.0.0.1:5150"
    net_info = machine_info.get_netinfo(server_url)
    print reg_obj.associate(machine_id, "blippy", net_info['ipaddr'], net_info['hwaddr'])






if __name__ == "__main__":
    main(sys.argv)


