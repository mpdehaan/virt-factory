#from pysqlite2 import dbapi2 as sqlite # actually db is sqlite 3.0
import sqlite
import SimpleXMLRPCServer

class XmlRpcInterface:

   def __init__(self):
       self.conn = sqlite.connect("/opt/shadowmanager/primary_db")
       self.cursor = self.conn.cursor()

   def login(self,user,password):
       # FIXME: placeholders
       self.cursor.execute("SELECT * FROM USERS WHERE username='%s' AND password='%s'" % (user,password))  
       results = self.cursor.fetchall()
       if len(results) >=1:
           return results[0][0]
       else:
           return -1

   # FIXME: these are rather inefficient for large result sets and will need upgrading later.
   # the API needs to be a lot smarter than this, this is mainly here to get things bootstrapped.
   def get_users(self):
       self.cursor.execute("SELECT * FROM users")
       results = self.cursor.fetchall()
       return results

   def get_machines(self):
       self.cursor.execute("SELECT * FROM machines")
       results = self.cursor.fetchall()
       return results

   def get_images(self):
       self.cursor.execute("SELECT * FROM images")
       results = self.cursor.fetchall()
       return results

   def get_deployments(self):
       self.cursor.execute("SELECT * FROM deployments")
       results = self.cursor.fetchall()
       return results


xmlrpc_interface = XmlRpcInterface()
server = SimpleXMLRPCServer.SimpleXMLRPCServer(("127.0.0.1", 5150))
server.register_instance(xmlrpc_interface)
server.serve_forever()
