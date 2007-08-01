#!/usr/bin/python
"""
Virt-factory backend code.

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

import SimpleXMLRPCServer
import os
import subprocess
import socket

SERVE_ON = (None,None)

# FIXME: logrotate

from codes import *

import config_data
import logger
import utils

from db import Database

from modules import task 
from modules import authentication
from modules import config
from modules import deployment
from modules import distribution
from modules import profile
from modules import machine
from modules import provisioning
from modules import registration
from modules import user
from modules import regtoken
from modules import puppet

from busrpc.services import RPCDispatcher
from busrpc.config import DeploymentConfig

from rhpl.translate import _, N_, textdomain, utf8
I18N_DOMAIN = "vf_server"


class Singleton(object):
    def __new__(type, *args, **kwargs):
        if not '_the_instance' in type.__dict__:
            type._the_instance = object.__new__(type, *args, **kwargs)
            type._the_instance.init(*args, **kwargs)
        return type._the_instance

class XmlRpcInterface(Singleton):

    def init(self):
        """
        Constructor sets up SQLAlchemy (database ORM) and logging.
        """
        config_obj = config_data.Config()
        self.config = config_obj.get()
       
        self.tables = {}
        self.tokens = []

        self.logger = logger.Logger().logger
        
        try:
            databases = self.config['databases']
            url = databases['primary']
            Database(url)
        except KeyError:
            # FIXME: update message after sqlalchemy conversion.
            comment =\
                'databases/secondary: temporarily required for sqlalchemy conversion'
            raise MisconfiguredException(comment=comment)

        self.__setup_handlers()
        self.auth = authentication.Authentication()
        self.auth.init_resources()
        
    def __setup_handlers(self):
        """
        Add RPC functions from each class to the global list so they can be called.
        FIXME: eventually calling most functions should go from here through getattr.
        """
        self.handlers = {}
        for x in [user, machine,
                  profile, deployment,
                  distribution,config,
                  provisioning, registration,
                  authentication, task, regtoken, puppet,]:
            x.register_rpc(self.handlers)
            self.logger.debug("adding %s" % x)

            # FIXME: find some more elegant way to surface the handlers?
            # FIXME: aforementioned login/session token requirement

    def get_dispatch_method(self, method):
        if method in self.handlers:
            return VfApiMethod(self.logger, self.auth, method,
                               self.handlers[method])
      
        else:
            self.logger.info("Unhandled method call for method: %s " % method)
            raise InvalidMethodException

    def _dispatch(self, method, params):
        """
        the SimpleXMLRPCServer class will call _dispatch if it doesn't
        find a handler method 
        """
        return self.get_dispatch_method(method)(*params)

class BusRpcWrapper:
    
    def __init__(self, config):
        self.rpc_interface = None

    def __getattr__(self, name):
        if self.rpc_interface == None:
            self.rpc_interface = XmlRpcInterface()
        return self.rpc_interface.get_dispatch_method(name)

    def __repr__(self):
        return ("<BusRpcWrapper>")

class VfApiMethod:
    def __init__(self, logger, auth, name, method):
        self.logger = logger
        self.auth = auth
        self.__method = method
        self.__name = name
        
    def __log_exc(self):
        """
        Log an exception.
        """
        (t, v, tb) = sys.exc_info()
        self.logger.info("Exception occured: %s" % t )
        self.logger.info("Exception value: %s" % v)
        self.logger.info("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))

    def __call__(self, *args):
        self.logger.debug("(X) -------------------------------------------")
        self.logger.debug("methods: %s params: %s" % (self.__name, args))
        try:
            # why aren't these auth checked? well...
            # user_login is where you get the
            #   auth token from in the first places
            # token_check is what validates the token
            # register can
            #   take authtokens or regtokens, so they do there own
            # auth check
            if self.__name not in ["user_login", "token_check", "register_system", "sign_node_cert" , "puppet_node_info" ]:
                self.auth.token_check(args[0])
            rc = self.__method(*args)
        except VirtFactoryException, e:
            self.__log_exc()
            rc = e
        except:
            self.logger.debug("Not a virt-factory specific exception")
            self.__log_exc()
            raise
        rc = rc.to_datastruct()
        self.logger.debug("Return code for %s: %s" % (self.__name, rc))
        return rc


def serve(websvc):
     """
     Code for starting the XMLRPC service. 
     FIXME:  make this HTTPS (see RRS code) and make accompanying Rails changes..
     """
     server = VirtFactoryXMLRPCServer(('', 5150))
     server.register_instance(websvc)
     server.serve_forever()

def serve_qpid(config_path, register_with_bridge=True):
     """
     Code for starting the QPID RPC service. 
     """
     config = DeploymentConfig(config_path)
     dispatcher = RPCDispatcher(config, register_with_bridge)
     
     try:
         dispatcher.start()
     except KeyboardInterrupt:
         dispatcher.stop()
     print "Exiting..."

class VirtFactoryXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
    def __init__(self, args):
       self.allow_reuse_address = True
       SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self, args)
      
def main(argv):
    """
    Start things up.
    """

    if "bridge" in sys.argv or "--bridge" in sys.argv:
        if "daemon" in sys.argv or "--daemon" in sys.argv:
            utils.daemonize("/var/run/vf_server_bridge.pid")
            serve_qpid("/etc/virt-factory/qpid-bridge.conf", register_with_bridge=False)
        else:
            print "serving...\n"
            # daemonize only if --daemonize, because I forget to type "debug" -- MPD
            serve_qpid("/etc/virt-factory/qpid-bridge.conf", register_with_bridge=False)
    else:
        websvc = XmlRpcInterface()
    
        for arg in sys.argv:
            if arg == "import" or arg == "--import":
                prov_obj = provisioning.Provisioning()
                prov_obj.init(None, {})
                return
            elif arg == "sync" or arg == "--sync":
                prov_obj = provisioning.Provisioning()
                prov_obj.sync(None, {}) # just for testing
                return
        if "qpid" in sys.argv or "--qpid" in sys.argv:
            if "daemon" in sys.argv or "--daemon" in sys.argv:
                utils.daemonize("/var/run/vf_server_qpid.pid")
                serve_qpid("/etc/virt-factory/qpid.conf")
            else:
                print "serving...\n"
                # daemonize only if --daemonize, because I forget to type "debug" -- MPD
                serve_qpid("/etc/virt-factory/qpid.conf")
        elif "daemon" in sys.argv or "--daemon" in sys.argv:
            utils.daemonize("/var/run/vf_server.pid")
            serve(websvc)
        else:
            print "serving...\n"
            # daemonize only if --daemonize, because I forget to type "debug" -- MPD
            serve(websvc)
       
# FIXME: upgrades?  database upgrade logic would be nice to have here, as would general creation (?)
# FIXME: command line way to add a distro would be nice to have in the future, rsync import is a bit heavy handed.
#        (and might not be enough for RHEL, but is good for Fedora/Centos)


if __name__ == "__main__":
    textdomain(I18N_DOMAIN)
    main(sys.argv)


