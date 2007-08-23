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
   
    

