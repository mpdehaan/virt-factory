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
import signal
import socket
import select

from rhpl.translate import _, N_, textdomain, utf8
I18N_DOMAIN = "vf_node_server"
SLEEP_INTERVAL = 60 * 1000 # 60 seconds to re-poll status if no wakeup call (FIXME: make longer)
SERVE_ON = (None,None)

# FIXME: this app writes a logfile in /var/log/virt-factory/svclog -- package should use logrotate
# FIXME: log setting in /var/log/virt-factory/svclog shouldn't be "DEBUG" for production use
# FIXME: /opt/log/virt-factory/svclog should be /var/log/virt-factory/svc.log


from codes import *

import config_data
import logger
import module_loader
import utils
import virt_utils
import amqp_utils
import time

from busrpc.services import RPCDispatcher
from busrpc.config import DeploymentConfig

MODULE_PATH="modules/"
modules = module_loader.load_modules(MODULE_PATH)

import string
import traceback

class Singleton(object):
    def __new__(type, *args, **kwargs):
        if not '_the_instance' in type.__dict__:
            type._the_instance = object.__new__(type, *args, **kwargs)
            type._the_instance.init(*args, **kwargs)
        return type._the_instance

def make_logger():
        return logger.Logger().logger

class XmlRpcInterface(Singleton):

    def init(self):
        """
        Constructor.
        """

        config_obj = config_data.Config()
        self.config = config_obj.get()
       
        self.logger = make_logger()

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
        return v

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
            rc = UncaughtException(traceback=traceback.format_exc())
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

def serve_status():

     # serve monitoring status for the current node, and
     # if applicable, any sub-nodes (guests)

     # FIXME: if libvirt is not installed, we have nothing to do here
     # and can save resources.  Note that if we start to do other
     # logging this /must/ change.

     watch_handle = open("/var/lib/virt-factory-nodes/watch","r")
     poller = select.poll()
     poller.register(watch_handle)

     logger = make_logger()
     
     if not os.path.exists("/etc/rc.d/init.d/libvirtd"):
         logger.info("disabling virt status loop as libvirt is not installed")
         return

     # establish upstream qpid connection
     amqp_conn = amqp_utils.VirtFactoryAmqpConnection()
     amqp_conn.connect()

     # ask server which nodes to start.
     virt_conn = virt_utils.VirtFactoryLibvirtConnection()
     vms = virt_conn.find_vm(-1)
     for vm in vms:
         name = vm.name().replace("_",":").upper()
         details = None
         try:
             (retcode, details) = amqp_conn.server.deployment_get_by_mac_address("UNSET",{ "mac_address" : name})
         #re-raise these, as that's how the server shuts down
         except KeyboardInterrupt:
             raise
         except:
             # can't figure out to auto start this one...
             (t, v, tb) = sys.exc_info()
             logger.info("Exception occured: %s" % t )
             logger.info("Exception value: %s" % v)
             logger.info("Exception info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
             logger.info("skipping vm auto-start (error): %s" % name)

         # FIXME: check to see if this machine is actually supposed to
         # be auto-started instead of starting all of them that are
         # under virt-factory's control.  We may want some to stay off.
         # check "details" for this.

         if retcode != 0 or not details.has_key("data"):
             # error
             logger.info("skipping vm auto-start (error2): %s" % name)
             continue
         if len(details['data']) <= 0:
             # no results
             logger.info("skipping vm auto-start (error3): %s" % name)
             continue
         if details['data'][0].has_key("auto_start") and details['data'][0]["auto_start"] == 0: 
             # this one is flagged to stay off
             logger.info("skipping vm auto-start (disabled by user): %s" % name)
             continue

         state = virt_conn.get_status2(vm)
         if state == "shutdown" or state == "crashed":
             logger.info("trying to auto-start vm: %s" % name)
             vm.create()


     all_status = {}

     while True:
         try:
             try:
                 # reconnect each time to avoid errors
                 virt_conn = virt_utils.VirtFactoryLibvirtConnection()
             #re-raise these, as that's how the server shuts down
             except KeyboardInterrupt:
                 raise
             except:
                 logger.error("libvirt connection failed")
                 continue         

             vms = virt_conn.find_vm(-1)
             for vm in vms:
                 send_it = True
                 status = virt_conn.get_status2(vm)
                 name = vm.name()

                 # only send status when it changes, conserve network
                 # and keep the logs (if any) quiet

                 if not all_status.has_key(name):
                     send_it = True
                 elif all_status[name] != status:
                     send_it = True

                 if send_it:
                     all_status[name] = status

                 if send_it:
                     args = {
                         "mac_address" : name.replace("_",":"),
                         "state"       : status
                     }
                     logger.info("sending status: %s" % args)
                     amqp_conn.server.deployment_set_state("UNSET", args)
         
             # FIXME: this currently might not be working.  until then
             # we will sleep as normal.  

             time.sleep(60)  # don't send status very often

             # rc = poller.poll(SLEEP_INTERVAL, select.POLLIN|select.POLLPRI)
              

         #re-raise these, as that's how the server shuts down
         except KeyboardInterrupt:
             raise
         except:
             (t, v, tb) = sys.exc_info()
             logger.info("Exception occured: %s" % t )
             logger.info("Exception value: %s" % v)
             logger.info("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))




def main(argv):
    """
    Start things up.
    """
   
    # create watch file
    wf = open("/var/lib/virt-factory-nodes/watch","w+")
    wf.write("")
    wf.close()
 
    websvc = XmlRpcInterface()
    host = socket.gethostname()
     
    if "--daemon" in sys.argv:
        utils.daemonize("/var/run/vf_node_server.pid")

    pid = os.fork()
    if pid == 0:
        serve_qpid("/etc/virt-factory-nodes/qpid.conf")
    else:
        try:
            serve_status()
        except KeyboardInterrupt:
            print "caught interrupt"
            os.kill(pid, signal.SIGINT)
            os.waitpid(pid,0)
        

if __name__ == "__main__":
    _("test") # make gettext be quiet when there are no strings
    textdomain(I18N_DOMAIN)
    main(sys.argv)


