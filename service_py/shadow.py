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

from sqlalchemy import *
import SimpleXMLRPCServer
import os
import traceback
import time
import logging
import subprocess

DATABASE_PATH = "/opt/shadowmanager/primary_db"

# FIXME: this app writes a logfile in /opt/shadowmanager/svclog -- package should use logrotate
# FIXME: log setting in /opt/shadowmanager/svclog shouldn't be "DEBUG" for production use
# FIXME: /opt/shadowmanager/svclog should be /var/log/shadowmanager/svc.log
# FIXME: /opt/shadowmanager/primary_db should be /var/lib/shadowmanager/primary_db


from codes import *
from errors import *
import user
import event
import image
import deployment
import machine
import distribution
from pysqlite2 import dbapi2 as sqlite

class XmlRpcInterface:

   def __init__(self):
       """
       Constructor sets up SQLAlchemy (database ORM) and logging.
       """
       self.tables = {}
       self.tokens = []
       self.__setup_handlers()
       self.connection = sqlite.connect(DATABASE_PATH)
       self.cursor = self.connection.cursor()
       self.logger = logging.getLogger("svc")
       handler = logging.FileHandler("svclog", "a")
       formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
       handler.setFormatter(formatter)
       self.logger.addHandler(handler)
       self.logger.setLevel(logging.DEBUG)

   def __setup_handlers(self):
       """
       Add RPC functions from each class to the global list so they can be called.
       FIXME: eventually calling most functions should go from here through getattr.
       """
       self.handlers = {}
       for x in [user,machine,image,deployment,distribution]:
           x.register_rpc(self.handlers)

   # FIXME: find some more elegant way to surface the handlers?
   # FIXME: aforementioned login/session token requirement

   def user_login(self,user,password):
       """
       Wrapper around the user login code in user.py.
       If login succeeds, create a token and return it to the caller.
       """
       self.logger.debug("login attempt: %s" % user)
       try:
           (rc, data) = self.handlers["user_login"](self,user,password)
           if rc == 0:
               self.tokens.append([data,time.time()])
           return (rc, data)
       except ShadowManagerException, e:
           return from_exception(e)

   def token_check(self,token):
       """
       Validate that the token passed in to any method call other than user_login
       is correct, and if not, raise an Exception.  Note that all exceptions are
       caught in dispatch, so methods give failing return codes rather than XMLRPCFaults.
       This is a feature, mainly since Rails (and other language bindings) can better
       grok tracebacks this way.
       """
       self.logger.debug("token check")
       now = time.time()
       for t in self.tokens:
           # remove tokens older than 1/2 hour
           if (now - t[1]) > 1800:
               self.tokens.remove(t)
               raise TokenExpiredException()
           if t[0] == token:
               # update the expiration counter
               t[1] = time.time()
               #return SuccessException()
               return ERR_SUCCESS
       raise TokenInvalidException()

   #======================================================
   # lots of wrappers to API functions.  See __dispatch for details.
   # eventually this should be mapped to use getattr so this
   # will not be required.  user_login and token_check are notable
   # exceptions.  Also note that some XMLRPC functions take 2 arguments here
   # but in the modules, they all consistantly take 3.  This may possibly
   # benefit from cleanup later.

   def user_list(self,token,args={}):
       return self.__dispatch("user_list",token,args)

   def user_get(self, token, args):
       return self.__dispatch("user_get",token,args)

   def user_add(self, token, args):
       return self.__dispatch("user_add",token,args)

   def user_edit(self, token, args):
       return self.__dispatch("user_edit",token,args)

   def user_delete(self, token, args):
       return self.__dispatch("user_delete",token,args)
 
   def machine_list(self,token,args={}):
       return self.__dispatch("machine_list",token,args)

   def machine_get(self, token, args):
       return self.__dispatch("machine_get",token,args)

   def machine_add(self, token, args):
       return self.__dispatch("machine_add",token,args)

   def machine_edit(self, token, args):
       return self.__dispatch("machine_edit",token,args)

   def machine_delete(self, token, args):
       return self.__dispatch("machine_delete",token,args)
 
   def image_list(self,token,args={}):
       return self.__dispatch("image_list",token,args)

   def image_get(self, token, args):
       return self.__dispatch("image_get",token,args)

   def image_add(self, token, args):
       return self.__dispatch("image_add",token,args)

   def image_edit(self, token, args):
       return self.__dispatch("image_edit",token,args)

   def image_delete(self, token, args):
       return self.__dispatch("image_delete",token,args)
   
   def deployment_list(self,token,args={}):
       return self.__dispatch("deployment_list",token,args={})

   def deployment_get(self, token, args):
       return self.__dispatch("deployment_get",token,args)

   def deployment_add(self, token, args):
       return self.__dispatch("deployment_add",token,args)

   def deployment_edit(self, token, args):
       return self.__dispatch("deployment_edit",token,args)
   
   def deployment_delete(self, token, args):
       return self.__dispatch("deployment_delete",token,args)

   def distribution_get(self, token, args):
       return self.__dispatch("distribution_get", token, args)

   def distribution_list(self, token, args={}):
       return self.__dispatch("distribution_list",token,args)

   def distribution_add(self, token, args):
       return self.__dispatch("distribution_add",token,args)

   def distribution_edit(self, token, args):
       return self.__dispatch("distribution_edit",token,args)

   def distribution_delete(self, token, args):
       return self.__dispatch("distribution_delete",token,args)


   def __dispatch(self, method, token, args=[]):
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
       self.logger.debug("calling %s, args=%s" % (method,args))
       try:
           self.token_check(token)
           rc = self.handlers[method](self,args)
           return rc
       except ShadowManagerException, e:
           return from_exception(e)
       # this is nice in theory but I really want the real TB's now
       # may reconsider for later.
       #except Exception, e2:
       #    tb = traceback.format_exc()
       #    self.logger.error(tb)
       #    return from_exception(UncaughtException(tb))    

def database_reset():
    """
    Used for testing.  Not callable from the web service.
    """
    try:
        os.remove(DATABASE_PATH)
    except:
        pass
    
    p = DATABASE_PATH
    p1 = subprocess.Popen(["cat","../setup/schema.sql"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["sqlite3",p], stdin=p1.stdout, stdout=subprocess.PIPE)
    p2.communicate()[0]
    p3 = subprocess.Popen(["cat","../setup/populate.sql"], stdout=subprocess.PIPE)
    p4 = subprocess.Popen(["sqlite3",p], stdin=p3.stdout, stdout=subprocess.PIPE)
    p4.communicate()[0]

def serve():
    """
    Code for starting the XMLRPC service. 
    FIXME:  make this HTTPS (see RRS code) and make accompanying Rails changes..
    """
    xmlrpc_interface = XmlRpcInterface()
    server = SimpleXMLRPCServer.SimpleXMLRPCServer(("127.0.0.1", 5150))
    server.register_instance(xmlrpc_interface)
    server.serve_forever()

if __name__ == "__main__":
    """
    Start things up.
    """
    # testmode() # temporary ...
    serve()


