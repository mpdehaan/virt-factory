from sqlalchemy import *
import SimpleXMLRPCServer
import os
import traceback
import time

# FIXME: write a dispatcher to move API's into categories based on class
# FIXME: all API's should require a login token that is *not* the user id. (session table, likely).

from codes import *
import user
import event
import image
import deployment
import machine


class XmlRpcInterface:

   def __init__(self):
       os.chdir("/opt/shadowmanager")
       self.db = create_engine("sqlite:///primary_db")
       self.meta = BoundMetaData(self.db)
       self.tables = {}
       self.__setup_tables()
       self.__setup_handlers()
       self.tokens = []
       self.session = create_session()

   def __setup_tables(self):
       m = self.meta
       self.tables = {
           "users"       : user.make_table(m),
           "events"      : event.make_table(m),
           "images"      : image.make_table(m),
           "deployments" : deployment.make_table(m),
           "machines"    : machine.make_table(m)
       } 

   def __setup_handlers(self):
       self.handlers = {}
       user.register_rpc(self.handlers)
       # others ...

   # FIXME: find some more elegant way to surface the handlers?
   # FIXME: aforementioned login/session token requirement

   def user_login(self,user,password):
       (success, rc, data) = self.handlers["user_login"](self.session,user,password)
       if success:
           self.tokens.append([data,time.time()])
       return (success, rc, data)

   def __token_check(self,token):
       now = time.time()
       for t in self.tokens:
           # remove tokens older than 1/2 hour
           if (now - t[1]) > 1800:
               self.tokens.remove(t)
               return result(ERR_TOKEN_EXPIRED)
           if t[0] == token:
               # update the expiration counter
               t[1] = time.time()
               return result(ERR_SUCCESS)
       return result(ERR_TOKEN_INVALID)

   def user_list(self,token):
       # FIXME: avoid duplication of these next 2 lines.
       check = self.__token_check(token)
       if not check[0]: return check
       return self.handlers["user_list"](self.session)

   def user_add(self, token, args):
       check = self.__token_check(token)
       if not check[0]: return check
       return self.handlers["user_add"](self.session,args)

   def user_edit(self, token, args):
       check = self.__token_check(token)
       if not check[0]: return check
       return self.handlers["user_edit"](self.session,args)
 
   def user_get(self, token, id):
       check = self.__token_check(token)
       if not check[0]: return check
       return self.handlers["user_get"](self.session,id)
 
   def user_delete(self, token, id):
       check = self.__token_check(token)
       if not check[0]: return check
       return self.handlers["user_delete"](self.session,id)
 
   def machine_list(self, token):
       check = self.__token_check(token)
       if not check[0]: return check
       return []

   def image_list(self, token):
       check = self.__token_check(token)
       if not check[0]: return check
       return []

   def deployment_list(self, token):
       check = self.__token_check(token)
       if not check[0]: return check
       return []

def serve():
    xmlrpc_interface = XmlRpcInterface()
    server = SimpleXMLRPCServer.SimpleXMLRPCServer(("127.0.0.1", 5150))
    server.register_instance(xmlrpc_interface)
    server.serve_forever()

def testmode():
    intf = XmlRpcInterface()
    (success, rc, token) = intf.user_login("guest","guest")
    print (success, rc, token)
    print intf.user_add(token,{
          "username" : "x",
          "first" : "x",
          "middle" : "x",
          "last" : "x",
          "description" : "x",
          "email" : "x",
          "password" : "x"
    })
    users = intf.user_list(token)
    print users
    for x in users[2]:
       if x["username"] != "guest":
           intf.user_delete(token,x["id"])
    users = intf.user_list(token)
    print users

if __name__ == "__main__":
    # testmode() # temporary ...
    serve()


