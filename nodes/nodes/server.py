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

import SimpleXMLRPCServer
import os
import socket
import glob

#socket.setdefaulttimeout(0)

from rhpl.translate import _, N_, textdomain, utf8
I18N_DOMAIN = "vf_node_server"
from M2Crypto import SSL
from M2Crypto.m2xmlrpclib import SSL_Transport, Server

SERVE_ON = (None,None)

# FIXME: this app writes a logfile in /var/log/virt-factory/svclog -- package should use logrotate
# FIXME: log setting in /var/log/virt-factory/svclog shouldn't be "DEBUG" for production use
# FIXME: /opt/log/virt-factory/svclog should be /var/log/virt-factory/svc.log


from codes import *

import config_data
import logger
import module_loader
import utils

MODULE_PATH="modules/"
modules = module_loader.load_modules(MODULE_PATH)
print modules

import string
import traceback

class XmlRpcInterface:

    def __init__(self):
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
              

    def __log_exc(self):
       """
       Log an exception.
       """
       (t, v, tb) = sys.exc_info()
       self.logger.debug("Exception occured: %s" % t )
       self.logger.debug("Exception value: %s" % v)
       self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
       
    def _dispatch(self, method, params):
       """
       the SimpleXMLRPCServer class will call _dispatch if it doesn't
       find a handler method 
       """
       if method == "call":
           method = params[0]
           params = params[1:] 
       if method in self.handlers:
           mh = self.handlers[method]
           self.logger.debug("(X) -------------------------------------------")
           self.logger.debug("methods: %s params: %s" % (method, params))
         
           try:
               rc = mh(*params)
           except VirtFactoryException, e:
               self.__log_exc()
               return e.to_datastruct()
           except:
               self.logger.debug("Not a virt-factory specific exception")
               self.__log_exc()
               raise
         
           self.logger.debug("Return code for %s: %s" % (method, rc.to_datastruct()))
           return rc.to_datastruct()
      
       else:
           self.logger.debug("Unhandled method call for method: %s with params: %s" % (method, params))
           raise InvalidMethodException


def serve(websvc,hostname):
     """
     Code for starting the XMLRPC service. 
     FIXME:  make this HTTPS (see RRS code) and make accompanying Rails changes..
     """
     print _("I think my hostname is: %s") % hostname
     ctx = initContext(hostname)
     server = VirtFactorySSLXMLRPCServer(ctx, (hostname, 2112))
     server.register_instance(websvc)
     server.serve_forever()

def sslCallback(*args):
   print args

def initContext(hostname):
    """
    Helper method for m2crypto's SSL libraries.
    """
    protocol = "sslv23"
    verify =  SSL.verify_peer|SSL.verify_fail_if_no_peer_cert
    verify_depth = 10
    ctx = SSL.Context(protocol)
    ctx.load_client_ca("/var/lib/puppet/ssl/certs/ca.pem")
    ctx.load_cert(
         certfile="/var/lib/puppet/ssl/certs/%s.pem" % hostname, 
         keyfile="/var/lib/puppet/ssl/private_keys/%s.pem" % hostname)
    ctx.load_verify_info("/var/lib/puppet/ssl/certs/ca.pem")
    ctx.set_verify(verify, verify_depth)
    ctx.set_session_id_ctx('xmlrpcssl')
    ctx.set_info_callback(sslCallback)
    return ctx


class SSLXMLRPCHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
   def finish(self):
      self.request.set_shutdown(SSL.SSL_RECEIVED_SHUTDOWN | SSL.SSL_SENT_SHUTDOWN)
      self.request.close()


class VirtFactorySSLXMLRPCServer(SSL.SSLServer, SimpleXMLRPCServer.SimpleXMLRPCServer):
    def __init__(self, ssl_context, address, handler=None, handle_error=None):
       self.allow_reuse_address = True
       
       if handler is None: 
           handler = SSLXMLRPCHandler
            
       SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self, address, handler)
       SSL.SSLServer.__init__(self, address, handler, ssl_context)
       self.instance = None
       self.logRequest = 5

    def errorHandler(self, *args):
       print args

       
def main(argv):
    """
    Start things up.
    """
    
    websvc = XmlRpcInterface()
    host = socket.gethostname()
     
    if "--daemon" in sys.argv:
        utils.daemonize("/var/run/vf_node_server.pid")
        serve(websvc,host)
    else:
        print _("serving...\n")
        serve(websvc,host)


if __name__ == "__main__":
    _("test") # make gettext be quiet when there are no strings
    textdomain(I18N_DOMAIN)
    main(sys.argv)


