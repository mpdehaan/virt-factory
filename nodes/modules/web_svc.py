#!/usr/bin/python

## Virt-factory backend code.
##
## Copyright 2006, Red Hat, Inc
## Adrian Likins <alikins@redhat.com
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
##

from nodes.codes import *

from nodes import config_data
from nodes import logger


import os
import threading
import time
import traceback
import socket

from busrpc.rpc import lookup_service
from busrpc.crypto import CertManager
import busrpc.qpid_transport

class WebSvc(object):
    def __init__(self):

        config_obj = config_data.Config()
        config_result = config_obj.get()
        self.config = config_result
        self.__init_log()
        self.logger.info("getting details...")
        self.__target = self.__get_file_data("/etc/sysconfig/virt-factory/server")
        self.logger.info("server: %s" % self.__target)
        self.__source = socket.gethostname()
        self.logger.info("client: %s" % self.__source)

        # FIXME: disabling until hang can be removed
        # FIXME: this part should be Singletonized (TM)

        #self.logger.info("connecting to QPID...")
        #self.server = Server(client=self.__source, host=self.__target)
        #self.logger.info("connected")

    def __get_file_data(self, fname):
        fileh = open(fname, "r")
        data = fileh.read()
        fileh.close()
        return data.strip()

    def __init_log(self):
        log = logger.Logger()
        self.logger = log.logger

class AuthWebSvc(WebSvc):
    def __init__(self):
        WebSvc.__init__(self)

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
