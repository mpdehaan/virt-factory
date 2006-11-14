from sqlalchemy import *
import SimpleXMLRPCServer
import os

# FIXME: write a dispatcher to move API's into categories based on class
# FIXME: all API's should require a login token that is *not* the user id. (session table, likely).

class User(object):
 
   def to_datastruct(self):
      return {
         "id"          : self.id,
         "username"    : self.username,
         "first"       : self.first,
         "middle"      : self.middle,
         "last"        : self.last,
         "description" : self.description,
         "email"       : self.email
      }

   pass

class XmlRpcInterface:

   def __init__(self):
       os.chdir("/opt/shadowmanager")
       self.db = create_engine("sqlite:///primary_db")
       self.meta = BoundMetaData(self.db)
       self.tables = {}
       self.__setup_tables()
       self.session = create_session()
       # testing only ...
       print self.login("guest","guest") 
       raise "heck"

   def __setup_tables(self):

       self.tables["users"] = self.__create_table(
           Table('users', self.meta,
               Column('id', Integer, primary_key=True),
               Column('username', String(255)),
               Column('password', String(255)),
               Column('first', String(255)),
               Column('middle', String(255)),
               Column('last', String(255)),
               Column('description', String(255)),
               Column('email', String(255))
           ), 
           User
       )
       """
       self.tables["audits"] = self.__create_table(
          Table("audits", self.meta,
               Column('id', Integer, primary_key=True),
               Column('time', String(255)),
               Column('user_id', Integer),
               Column('feature_id', Integer),
               Column('action', String(255)),
               Column('user_comment', String(255))
          )
       )
       self.tables["images"] = self.__create_table(
          Table("images", self.meta,
               Column('id', Integer, primary_key=True), 
               Column('name', String(255)),
               Column('version', String(255)),
               Column('filename', String(255)),
               Column('specfile', String(255)),
          )
       )
       """

   def __create_table(self,table,mapclass):
       try:
           table.create()
       except exceptions.SQLError:
           # FIXME: need to trap "already exists" only.
           pass
       if mapper is not None:
           mapper(mapclass, table)
       return table

   def login(self,user,password):
       query = self.session.query(User)
       sel = query.select(User.c.username.in_(user))
       if len(sel) == 0 or sel[0].password != password:
            return -1
       else:
            return sel[0].id

   # FIXME: these are rather inefficient for large result sets and needs to support partial ranges
   def get_users(self):
       query = self.session.query(User)
       sel = query.select()
       return [x.to_datastruct() for x in sel]

   def add_user(self, args):
       user = User()
       # FIXME: input should be a hash, not a long list of vars
       user.username = args["username"]
       user.password = args["password"]
       user.first = args["first"]
       user.middle = args["middle"]
       user.last = args["last"]
       user.description = args["description"]
       user.email = args["email"]
       # FIXME: we'd want to do validation here (actually in the User class) 
       self.session.save(user)
       return user in self.session 
 
   def delete_user(self, id):
      """
      try: 
           self.cursor.execute("DELETE FROM USERS WHERE id = " % (id))
           return self.cursor.fetchall()
      except Exception, e:
           return str(e)
      """
      query = self.session.query(User)
      user = query.get_by(User.c.id.in_(id))
      self.session.delete(user)
      return not user in session  
 
   def get_machines(self):
       """
       self.cursor.execute("SELECT * FROM machines")
       results = self.cursor.fetchall()
       return results
       """ 
       return -1

   def get_images(self):
       """
       self.cursor.execute("SELECT * FROM images")
       results = self.cursor.fetchall()
       return results
       """
       return -1

   def get_deployments(self):
       """
       self.cursor.execute("SELECT * FROM deployments")
       results = self.cursor.fetchall()
       return results
       """
       return -1

xmlrpc_interface = XmlRpcInterface()
server = SimpleXMLRPCServer.SimpleXMLRPCServer(("127.0.0.1", 5150))
server.register_instance(xmlrpc_interface)
server.serve_forever()
