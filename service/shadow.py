"""
ShadowManager backend code.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import SimpleXMLRPCServer
import os
import subprocess
import time

from pysqlite2 import dbapi2 as sqlite

SERVE_ON = (None,None)

# FIXME: this app writes a logfile in /opt/shadowmanager/svclog -- package should use logrotate
# FIXME: log setting in /opt/shadowmanager/svclog shouldn't be "DEBUG" for production use
# FIXME: /opt/shadowmanager/svclog should be /var/log/shadowmanager/svc.log
# FIXME: /opt/shadowmanager/primary_db should be /var/lib/shadowmanager/primary_db


from codes import *

import config_data
import logger

from modules import action
from modules import authentication
from modules import config
from modules import deployment
from modules import distribution
from modules import image
from modules import machine
from modules import provisioning
from modules import registration
from modules import user



# this is kind of handy, so keep it around for now
# but we really need to fix out server side logging and error
# reporting so we don't need it
import string
import traceback
def trace_me():
   x = traceback.extract_stack()
   bar = string.join(traceback.format_list(x))
   return bar

class XmlRpcInterface:

   def __init__(self):
       """
       Constructor sets up SQLAlchemy (database ORM) and logging.
       """

       if not os.path.exists(config_data.CONFIG_FILE):
           print "\nNo %s found.\n" % config_data.CONFIG_FILE
           return

       config_obj = config_data.Config()
       self.config = config_obj.get()
       
       self.tables = {}
       self.tokens = []

       self.logger = logger.Logger().logger

       self.__setup_handlers()
       self.auth = authentication.Authentication()
       
   def __setup_handlers(self):
      """
       Add RPC functions from each class to the global list so they can be called.
       FIXME: eventually calling most functions should go from here through getattr.
       """
      self.handlers = {}
      for x in [user, machine,
                image, deployment,
                distribution,config,
                provisioning, registration,
                authentication, action]:
         x.register_rpc(self.handlers)
         self.logger.debug("adding %s" % x)

         # FIXME: find some more elegant way to surface the handlers?
         # FIXME: aforementioned login/session token requirement


   #======================================================
   # lots of wrappers to API functions.  See __dispatch for details.
   # eventually this should be mapped to use getattr so this
   # will not be required.  user_login and token_check are notable
   # exceptions.  Also note that some XMLRPC functions take 2 arguments here
   # but in the modules, they all consistantly take 3.  This may possibly
   # benefit from cleanup later.


   def __log_exc(self):
      (t, v, tb) = sys.exc_info()
      self.logger.debug("Exception occured: %s" % t )
      self.logger.debug("Exception value: %s" % v)
      self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
      
   # the SimpleXMLRPCServer class will call _dispatch if it doesn't
   # find a handler method 
   def _dispatch(self, method, params):
      # FIXME: eventually, this will be all of self.handlers 
      if method in self.handlers:
         mh = self.handlers[method]
         self.logger.debug("(X) -------------------------------------------")
         self.logger.debug("methods: %s params: %s" % (method, params))
         
         try:
            if method not in ["user_login", "token_check"]:
               self.auth.token_check(params[0])
            rc = mh(*params)
         except ShadowManagerException, e:
            self.__log_exc()
            return e.to_datastruct()
         except:
            self.logger.debug("Not a shadowmanager specific exception")
            self.__log_exc()
            raise
         
         self.logger.debug("return code for %s: %s" % (method, rc.to_datastruct()))
         return rc.to_datastruct()
      
      else:
         self.logger.debug("Got an unhandled method call for method: %s with params: %s" % (method, params))
         raise InvalidMethodException


def database_reset():
    """
    Used for testing.  Not callable from the web service.
    """
    DATABASE_PATH = "/var/lib/shadowmanager/primary_db"
    try:
        os.remove(DATABASE_PATH)
    except:
        pass
    
    p = DATABASE_PATH
    p1 = subprocess.Popen(["cat","../setup/schema.sql"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["sqlite3",p], stdin=p1.stdout, stdout=subprocess.PIPE)
    p2.communicate()
    p3 = subprocess.Popen(["cat","../setup/populate.sql"], stdout=subprocess.PIPE)
    p4 = subprocess.Popen(["sqlite3",p], stdin=p3.stdout, stdout=subprocess.PIPE)
    p4.communicate()

def serve(websvc):
    """
    Code for starting the XMLRPC service. 
    FIXME:  make this HTTPS (see RRS code) and make accompanying Rails changes..
    """
    server = ShadowXMLRPCServer(("127.0.0.1", 5150))
    server.register_instance(websvc)
    server.serve_forever()


class ShadowXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
   def __init__(self, args):
      self.allow_reuse_address = True
      SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self, args)
      

if __name__ == "__main__":
    """
    Start things up.
    """
    
    websvc = XmlRpcInterface()
     
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "init":
            config_obj = config_data.Config()
            config_obj.reset()
        elif sys.argv[1].lower() == "import":
            prov_obj = provisioning.Provisioning()
            prov_obj.init(None, {})
        elif sys.argv[1].lower() == "sync":
            # FIXME: this is just for testing and should be removed in prod.
            prov_obj = provisioning.Provisioning()
            prov_obj.sync(None, {})
        else:
            print """

            I'm sorry, I can't do that, Dave.

            Usage: shadow [import|sync]

            """
            sys.exit(1)
    else:
        print "serving...\n"
        serve(websvc)

    # FIXME: upgrades?  database upgrade logic would be nice to have here, as would general creation (?)
    # FIXME: command line way to add a distro would be nice to have in the future, rsync import is a bit heavy handed.
    #        (and might not be enough for RHEL, but is good for Fedora/Centos)



