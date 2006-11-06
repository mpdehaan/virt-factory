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

xmlrpc_interface = XmlRpcInterface()
server = SimpleXMLRPCServer.SimpleXMLRPCServer(("127.0.0.1", 5150))
server.register_instance(xmlrpc_interface)
server.serve_forever()
