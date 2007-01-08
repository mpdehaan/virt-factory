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
       
       self.dbpath = self.config["databases"]["primary"]

       self.tables = {}
       self.tokens = []

       self.logger = logger.Logger().logger

       self.__setup_handlers()
       self.connection = self.sqlite_connect()
       self.cursor = self.connection.cursor()
       self.auth = authentication.Authentication()
       

   def sqlite_connect(self):
      """Workaround for \"can't connect to full and/or unicode path\" weirdness"""
      
      current = os.getcwd() 
      os.chdir(os.path.dirname(self.dbpath))
      conn = sqlite.connect(os.path.basename(self.dbpath))
      os.chdir(current)
      return conn 
   
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
                authentication]:
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



   # the SimpleXMLRPCServer class will call _dispatch if it doesn't
   # find a handler method 
   def _dispatch(self, method, params):
      # FIXME: eventually, this will be all of self.handlers 
      if method in self.handlers:
         mh = self.handlers[method]
         self.logger.debug("methods: %s params: %s" % (method, params))
         print mh, method
         
         if method not in ["user_login", "token_check"]:
            print "\ncalling self.token_check\n", params
            self.auth.token_check(params)
            
         try:
            rc = mh(*params)
         except Exception, e:
            #FIXME: this is a bit lame, but it will help us debug stuff
            self.logger.debug("Exception occured: %s" % sys.exc_type )
            self.logger.debug("Exception value: %s" % sys.exc_value)
            self.logger.debug("%s" % e.format())
            raise
         except:
            self.logger.debug("Not a shadowmanager specific exception")
            self.logger.debug("Exception occured: %s" % sys.exc_type )
            self.logger.debug("Exception value: %s" % sys.exc_value)
            self.logger.debug("%s" % e.format())
            raise
         self.logger.debug("return code: %s" % rc)
         # FIXME: I really don't like this for some reason.
         # parse out the SuccessExpection, and return data in some
         # format that the client likes. I'd really like to see the methods
         # return data in the correct format directly. It's a bit more duplicated
         # code, but I think it makes it much easier to see whats going on.
         return rc.to_datastruct()
      else:
         print "unhandled method"
         print "method: ", method
         print "params: ", params


   def __dispatch(self, method, token, dispatch_args=[]):
       """
       Dispatch is a wrapper around all API functions other
       than user_login and token_check.  It is intended that
       there be no other exceptions to this rule.

       This function calls the registered API method and catches
       all exceptions, turing them (if subclassed from ShadowManagerException)
       into the proper return codes.  Uncaught exceptions are returned
       with an UNCAUGHT_EXCEPTION return code. 

       Since we are already logged in, we can send tracebacks to Ruby
       (the user is already valid, so it's not a security problem).

       Tracebacks are also logged in the configured log location.
       """ 
       self.logger.debug("calling %s, dispatch_=%s" % (method,dispatch_args))
       try:
           self.authentication.token_check(token)
           rc = self.handlers[method](self,dispatch_args)
           return rc.to_datastruct()
       except ShadowManagerException, e:
           return e.to_datastruct()


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
            # FIXME: do any other first time setup here...
            config.config_reset(websvc,{})
        elif sys.argv[1].lower() == "import":
            provisioning.provisioning_init(websvc,{})
        elif sys.argv[1].lower() == "sync":
            # FIXME: this is just for testing and should be removed in prod.
            provisioning.provisioning_sync(websvc,{})
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



