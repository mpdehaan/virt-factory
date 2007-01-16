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

import optparse
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
        rc = self.server.machine_new(self.token)

        print rc

        return rc

    # for a machine that has an id (either from the wui, or as part of the
    # generated kickstart, assosicate it with a hostname and ip_addr so that
    # taskotron can contact its node api
    def associate(self, machine_id, hostname, ip_addr, mac_addr):
        rc = self.server.machine_associate(self.token, machine_id, ip_addr, mac_addr)

        return rc


def main(argv):
    reg_obj = Register()

    reg_obj.login("admin", "fedora")
    machine_id = reg_obj.register()[1]['data']

    print machine_id
    
    print reg_obj.associate(machine_id, "blippy", "127.0.0.1", "AA:BB:CC:DD:EE:FF")

    
    



if __name__ == "__main__":
    main(sys.argv)


