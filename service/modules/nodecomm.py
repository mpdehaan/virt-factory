#!/usr/bin/python

"""
Laser Taskatron 3000
(aka Virt-factory-a-tron 3000 backend task scheduler code)

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Adrian Likins <alikins@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import sys

from busrpc.rpc import lookup_service
from busrpc.crypto import CertManager
import busrpc.qpid_transport

class Server:
    def __init__(self, client=None, node=None, server=None):
        transport = busrpc.qpid_transport.QpidTransport(host=server)
        transport.connect()

        # no crypto for now
        #cm = CertManager('/var/lib/virt-factory/qpidcert', client)
        cm = None
    
        self.rpc_interface = lookup_service("nodes", transport, host=node, server_name="busrpc.nodes", cert_mgr=cm, use_bridge=False)
        if self.rpc_interface == None:
            print "Lookup failed :("
            sys.exit(-1)    

    def __getattr__(self, name):
        return self.rpc_interface.__getattr__(name)

def main(args):
    hostfrom   = args[1]
    hostto     = args[2]
    hostserver = args[3]
    method     = args[4]
    method_args     = args[5:]
    print "----------------------------"
    print "vf_nodecomm"
    print "from        = ", hostfrom
    print "to          = ", hostto
    print "server      = ", hostserver
    print "method      = ", method
    print "method_args = ", method_args
    print "----------------------------"
    handle = Server(hostfrom, hostto, hostserver)
    real_args = []
    real_args.append(method)
    real_args.extend(method_args)
    rc = handle.call(*real_args)
    print rc
    return rc

if __name__ == "__main__":
    main(sys.argv)
