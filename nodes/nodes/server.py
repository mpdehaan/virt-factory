#!/usr/bin/python
"""
virt-factory client code.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>
Adrian Likins <alikins@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import os
import socket


from rhpl.translate import _, N_, textdomain, utf8
I18N_DOMAIN = "vf_node_server"

SERVE_ON = (None,None)

# FIXME: this app writes a logfile in /var/log/virt-factory/svclog -- package should use logrotate
# FIXME: log setting in /var/log/virt-factory/svclog shouldn't be "DEBUG" for production use
# FIXME: /opt/log/virt-factory/svclog should be /var/log/virt-factory/svc.log


from codes import *

import config_data
import logger
import module_loader
import utils

from busrpc.services import RPCDispatcher
from busrpc.config import DeploymentConfig

MODULE_PATH="modules/"
modules = module_loader.load_modules(MODULE_PATH)
print modules

import string
import traceback

class Singleton(object):
    def __new__(type, *args, **kwargs):
        if not '_the_instance' in type.__dict__:
            type._the_instance = object.__new__(type, *args, **kwargs)
            type._the_instance.init(*args, **kwargs)
        return type._the_instance

class XmlRpcInterface(Singleton):

    def init(self):
        """
        Constructor.
        """

        config_obj = config_data.Config()
        self.config = config_obj.get()
       
        self.logger = logger.Logger().logger

        self.__setup_handlers()
       
    def __setup_handlers(self):
        """
        Add RPC functions from each class to the global list so they can be called.
        FIXME: eventually calling most functions should go from here through getattr.
        """
        self.handlers = {}
        for x in modules.keys():
           try:
              modules[x].register_rpc(self.handlers)
              self.logger.debug("adding %s" % modules[x])
           except AttributeError, e:
              self.logger.warning("module %s could not be loaded, it did not have a register_rpc method" % modules[x])
              
    def get_dispatch_method(self, method):
        if method == "call":
            return VfApiMethod(self, method, None)
        elif method in self.handlers:
            return VfApiMethod(self, method, self.handlers[method])
        else:
            self.logger.info("Unhandled method call for method: %s " % method)
            print "Unhandled method call for method: %s " % method
            raise InvalidMethodException

    def _dispatch(self, method, params):
        """
        the SimpleXMLRPCServer class will call _dispatch if it doesn't
        find a handler method 
        """
        return self.get_dispatch_method(method)(*params)

class VfApiMethod:
    def __init__(self, rpc_interface, name, method):
        self.rpc_interface = rpc_interface
        self.__name = name
        self.__method = method
        
    def __log_exc(self):
        """
        Log an exception.
        """
        (t, v, tb) = sys.exc_info()
        self.rpc_interface.logger.info("Exception occured: %s" % t )
        self.rpc_interface.logger.info("Exception value: %s" % v)
        self.rpc_interface.logger.info("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))

    def __call__(self, *args):
        if self.__name == "call":
            return self.rpc_interface._dispatch(args[0], args[1:])
        self.rpc_interface.logger.debug("(X) -------------------------------------------")
        self.rpc_interface.logger.debug("methods: %s params: %s" % (self.__name, args))
        try:
            rc = self.__method(*args)
        except VirtFactoryException, e:
            self.__log_exc()
            rc = e
        except:
            self.rpc_interface.logger.debug("Not a virt-factory specific exception")
            self.__log_exc()
            rc = e
            #raise
        rc = rc.to_datastruct()
        self.rpc_interface.logger.debug("Return code for %s: %s" % (self.__name, rc))
        return rc

class BusRpcWrapper:
    
    def __init__(self, config):
        self.rpc_interface = None

    def __getattr__(self, name):
        if self.rpc_interface == None:
            self.rpc_interface = XmlRpcInterface()
        return self.rpc_interface.get_dispatch_method(name)

    def __repr__(self):
        return ("<BusRpcWrapper>")

def serve_qpid(config_path):
     """
     Code for starting the QPID RPC service. 
     """
     config = DeploymentConfig(config_path)
     server_file = open("/etc/sysconfig/virt-factory/server","r")
     server_host = server_file.read()
     server_file.close()
     dispatcher = RPCDispatcher(config, server_host=server_host, register_with_bridge=False, is_bridge_server=False)
     
     try:
         dispatcher.start()
     except KeyboardInterrupt:
         dispatcher.stop()
     print "Exiting..."

def main(argv):
    """
    Start things up.
    """
    
    websvc = XmlRpcInterface()
    host = socket.gethostname()
     
    if "--daemon" in sys.argv:
        utils.daemonize("/var/run/vf_node_server.pid")
    else:
        print _("serving...\n")
    serve_qpid("/etc/virt-factory-nodes/qpid.conf")


if __name__ == "__main__":
    _("test") # make gettext be quiet when there are no strings
    textdomain(I18N_DOMAIN)
    main(sys.argv)


