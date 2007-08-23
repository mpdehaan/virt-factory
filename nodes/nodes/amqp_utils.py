# Utility functions for dealing with libvirt, whether from
# the remote API or the polling scripts

"""
Virt-factory backend code.

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
import os
import subprocess
from nodes.codes import *
import threading
import time
import traceback
import socket
from busrpc.rpc import lookup_service
from busrpc.crypto import CertManager
import busrpc.qpid_transport
import config_data

class VirtFactoryAmqpConnection():

    def __init__(self,connect_later=False):

        config_obj = config_data.Config()
        config_result = config_obj.get()
        self.config = config_result
        self.__target = self.__get_file_data("/etc/sysconfig/virt-factory/server")
        self.__source = socket.gethostname()
        self.server_initialized = False
       

    def connect(self):
        if not self.server_initialized:
            self.server = Server(client=self.__source, host=self.__target)
            self.server_initialized = True
        return self.server

    def __get_file_data(self, fname):
        fileh = open(fname, "r")
        data = fileh.read()
        fileh.close()
        return data.strip()
   
    
# this class is for AMQP communication to the parent server
# borrowed from vf_register's source

class Server:
    def __init__(self, client=None, host=None):
        transport = busrpc.qpid_transport.QpidTransport(host=host)
        transport.connect()

        # no crypto for now
        #cm = CertManager('/var/lib/virt-factory/qpidcert', client)
        cm = None
        self.rpc_interface = lookup_service("rpc", transport, host=host, server_name="busrpc.virt-factory", cert_mgr=cm, use_bridge=False)
        if self.rpc_interface == None:
            print "Lookup failed :("
            sys.exit(-1)

    def __getattr__(self, name):
        return self.rpc_interface.__getattr__(name)

