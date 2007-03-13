#!/usr/bin/python

"""
Laser Taskatron 3000
(aka Virt-factory-a-tron 3000 backend task scheduler code)

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Adrian Likins <alikins@redhat.com>
Scott Seago <sseago@redhat.com>

XMLRPCSSL portions based on http://linux.duke.edu/~icon/misc/xmlrpcssl.py

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import sys
import socket

from M2Crypto import SSL
from M2Crypto.m2xmlrpclib import SSL_Transport, Server
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

# FIXME: fromhost should be taken from a settings file or other source
# not passed in, which could cause problems with systems that have
# multiple hostnames and an unpredictable return for socket.gethostname
# especially when mixed in with the puppet cert stuff that may only create
# one pem file for a specific hostname.

def get_handle(fromhost, target):
    """
    Return a xmlrpc server object for a given hostname.
    """
    print "****************************** GET HANDLE "
    my_ctx = SSL.Context('sslv23')

    print "FROM: %s" % fromhost
        
    # Load CA cert
    my_ctx.load_client_ca("/var/lib/puppet/ssl/ca/ca_crt.pem")

    # Load target cert ...
    # FIXME: paths
    print "loading certs for: %s" % fromhost
       
    my_ctx.load_cert(
       certfile="/var/lib/puppet/ssl/certs/%s.pem" % fromhost,
       keyfile="/var/lib/puppet/ssl/private_keys/%s.pem" % fromhost
    )

    my_ctx.set_session_id_ctx('xmlrpcssl')

    #ctx.set_info_callback(callback)

    print "target is: %s" % target
 
    my_uri = "https://%s:2112" % target
    print "contacting: %s" % my_uri
    my_rserver = Server(my_uri, SSL_Transport(ssl_context = my_ctx))
    print my_rserver
    return my_rserver 

def main(args):
    hostfrom = args[1]
    hostto   = args[2]
    method   = args[3]
    method_args     = args[4:]
    print "----------------------------"
    print "vf_nodecomm"
    print "from        = ", hostfrom
    print "to          = ", hostto
    print "method      = ", method
    print "method_args = ", method_args
    print "----------------------------"
    handle = get_handle(hostfrom, hostto)
    real_args = []
    real_args.append(method)
    real_args.extend(method_args)
    rc = handle.call(*real_args)
    print rc
    return rc

if __name__ == "__main__":
    main(sys.argv)

