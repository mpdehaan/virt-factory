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


#import os
import string
#import traceback
import sys
#import glob
import socket

from M2Crypto import SSL
from M2Crypto.m2xmlrpclib import SSL_Transport, Server
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

def get_handle(target):
    """
    Return a xmlrpc server object for a given hostname.
    """
    print "****************************** GET HANDLE "
    ctx = SSL.Context('sslv23')

    fromhost = socket.gethostname()
    print "FROM: %s" % fromhost
        
    # Load CA cert
    ctx.load_client_ca("/var/lib/puppet/ssl/ca/ca_crt.pem")

    # Load target cert ...
    # FIXME: paths
    print "loading certs for: %s" % fromhost
       
    ctx.load_cert(
       certfile="/var/lib/puppet/ssl/certs/%s.pem" % fromhost,
       keyfile="/var/lib/puppet/ssl/private_keys/%s.pem" % fromhost
    )

    ctx.set_session_id_ctx('xmlrpcssl')

    #ctx.set_info_callback(callback)

    print "target is: %s" % target
 
    uri = "https://%s:2112" % target
    print "contacting: %s" % uri
    rserver = Server(uri, SSL_Transport(ssl_context = ctx))
    print rserver
    return rserver 

