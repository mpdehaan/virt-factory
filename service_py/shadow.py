from sqlalchemy import *
import SimpleXMLRPCServer
import os

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
       # testing only ...
       print self.user_login("guest","guest") 
       print self.user_add({
          "username" : "x",
          "first" : "x",
          "middle" : "x",
          "last" : "x",
          "description" : "x",
          "email" : "x",
          "password" : "x"
       })
       raise "stop"

   def __setup_tables(self):
       m = self.__create_table
       self.tables = {
           "users"       : user.make_table(m,self.meta),
           "events"      : event.make_table(m,self.meta),
           "images"      : image.make_table(m,self.meta),
           "deployments" : deployment.make_table(m,self.meta),
           "machines"    : machine.make_table(m,self.meta)
       } 

   def __setup_handlers(self):
       self.handlers = {}
       user.register_rpc(self.handlers)
       # others ...

   def __create_table(self,mapclass,table):
       try:
           table.create()
       except exceptions.SQLError:
           pass
       if mapclass is not None:
           mapper(mapclass, table)
       return table

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

if __name__ == "__main__":
    serve()


