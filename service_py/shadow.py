from sqlalchemy import *
import SimpleXMLRPCServer
import os
import traceback

# FIXME: write a dispatcher to move API's into categories based on class
# FIXME: all API's should require a login token that is *not* the user id. (session table, likely).

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
       return self.handlers["user_login"](self.session,user,password)

   def user_list(self):
       return self.handlers["user_list"](self.session)

   def user_add(self, args):
       return self.handlers["user_add"](self.session,args)
 
   def user_delete(self, id):
       return self.handlers["user_delete"](self.session,id)
 
   def machine_list(self):
       return []

   def image_list(self):
       return []

   def deployment_list(self):
       return []

def serve():
    xmlrpc_interface = XmlRpcInterface()
    server = SimpleXMLRPCServer.SimpleXMLRPCServer(("127.0.0.1", 5150))
    server.register_instance(xmlrpc_interface)
    server.serve_forever()

def testmode():
    intf = XmlRpcInterface()
    print intf.user_login("guest","guest")
    print intf.user_add({
          "username" : "x",
          "first" : "x",
          "middle" : "x",
          "last" : "x",
          "description" : "x",
          "email" : "x",
          "password" : "x"
    })
    users = intf.user_list()
    print users
    for x in users:
       if x["username"] != "guest":
           intf.user_delete(x["id"])
    users = intf.user_list()
    print users
    raise "stop"

if __name__ == "__main__":
    testmode() # temporary ...
    serve()


