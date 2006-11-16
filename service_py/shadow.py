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


class XmlRpcInterface:

   def __init__(self):
       """
       Constructor sets up SQLAlchemy (database ORM) and logging.
       """
       os.chdir("/opt/shadowmanager")
       self.db = create_engine("sqlite:///primary_db")
       self.meta = BoundMetaData(self.db)
       self.tables = {}
       self.__setup_tables()
       self.__setup_handlers()
       self.tokens = []
       self.session = create_session()
       self.logger = logging.getLogger("svc")
       handler = logging.FileHandler("svclog", "a")
       formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
       handler.setFormatter(formatter)
       self.logger.addHandler(handler)
       self.logger.setLevel(logging.DEBUG)

   def __setup_tables(self):
       """
       This function creates SQLAlchemy table objects for each managed table.
       """
       m = self.meta
       self.tables = {
           "users"       : user.make_table(m),
           "events"      : event.make_table(m),
           "images"      : image.make_table(m),
           "deployments" : deployment.make_table(m),
           "machines"    : machine.make_table(m)
       } 

   def __setup_handlers(self):
       """
       Add RPC functions from each class to the global list so they can be called.
       FIXME: eventually calling most functions should go from here through getattr.
       """
       self.handlers = {}
       user.register_rpc(self.handlers)
       machine.register_rpc(self.handlers)
       image.register_rpc(self.handlers)
       # others ...

   # FIXME: find some more elegant way to surface the handlers?
   # FIXME: aforementioned login/session token requirement

   def user_login(self,user,password):
       """
       Wrapper around the user login code in user.py.
       If login succeeds, create a token and return it to the caller.
       """
       self.logger.debug("login attempt: %s" % user)
       try:
           (success, rc, data) = self.handlers["user_login"](self.session,user,password)
           if success:
               self.tokens.append([data,time.time()])
           return (success, rc, data)
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
               raise ExpiredTokenException()
           if t[0] == token:
               # update the expiration counter
               t[1] = time.time()
               return SuccessException()
       raise TokenInvalidException()

   #======================================================
   # lots of wrappers to API functions.  See __dispatch for details.
   # eventually this should be mapped to use getattr so this
   # will not be required.  user_login and token_check are notable
   # exceptions.  Also note that some XMLRPC functions take 2 arguments here
   # but in the modules, they all consistantly take 3.  This may possibly
   # benefit from cleanup later.

   def user_list(self,token):
       return self.__dispatch("user_list",token,{})

   def user_get(self, token, args):
       return self.__dispatch("user_get",token,args)

   def user_add(self, token, args):
       return self.__dispatch("user_add",token,args)

   def user_edit(self, token, args):
       return self.__dispatch("user_edit",token,args)

   def user_delete(self, token, args):
       return self.__dispatch("user_delete",token,args)
 
   def machine_list(self,token):
       return self.__dispatch("machine_list",token,{})

   def machine_get(self, token, args):
       return self.__dispatch("machine_get",token,args)

   def machine_add(self, token, args):
       return self.__dispatch("machine_add",token,args)

   def machine_edit(self, token, args):
       return self.__dispatch("machine_edit",token,args)

   def machine_delete(self, token, args):
       return self.__dispatch("machine_delete",token,args)
 
   def image_list(self,token):
       return self.__dispatch("image_list",token,{})

   def image_get(self, token, args):
       return self.__dispatch("image_get",token,args)

   def image_add(self, token, args):
       return self.__dispatch("image_add",token,args)

   def image_edit(self, token, args):
       return self.__dispatch("image_edit",token,args)

   def image_delete(self, token, args):
       return self.__dispatch("image_delete",token,args)
 
   def deployment_list(self, token):
       # FIXME
       return SuccessException([])

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
           return self.handlers[method](self.session,args)
       except ShadowManagerException, e:
           return from_exception(e)
       except Exception, e2:
           tb = traceback.format_exc()
           self.logger.error(tb)
           return from_exception(UncaughtException(tb))    

def serve():
    """
    Code for starting the XMLRPC service. 
    FIXME:  make this HTTPS (see RRS code) and make accompanying Rails changes..
    """
    xmlrpc_interface = XmlRpcInterface()
    server = SimpleXMLRPCServer.SimpleXMLRPCServer(("127.0.0.1", 5150))
    server.register_instance(xmlrpc_interface)
    server.serve_forever()

def testmode():
    """
    This is just a throw-away function for testing outside of XMLRPC context.
    It can be deleted or mangled however needed.
    """
    intf = XmlRpcInterface()
    (success, rc, token) = intf.user_login("guest","guest")
    print 1 
    print (success, rc, token)
    print 2 
    print intf.user_add(token,{
          "username" : "x",
          "first" : "x",
          "middle" : "x",
          "last" : "x",
          "description" : "x",
          "email" : "x",
          "password" : "x"
    })
    print 3
    users = intf.user_list(token)
    print 4
    print users
    print 5
    for x in users[2]:
       if x["username"] != "guest":
           intf.user_delete(token,x)
    print 6 
    users = intf.user_list(token)
    print 7
    print users

if __name__ == "__main__":
    """
    Start things up.
    """
    # testmode() # temporary ...
    serve()


