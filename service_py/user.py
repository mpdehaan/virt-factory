from sqlalchemy import *
import time

def make_table(creator, meta):
    return creator(User, Table('users', meta,
        Column('id', Integer, primary_key=True),
        Column('username', String(255)),
        Column('password', String(255)),
        Column('first', String(255)),
        Column('middle', String(255)),
        Column('last', String(255)),
        Column('description', String(255)),
        Column('email', String(255))
     ))
   
def user_login(session,user,password):
     query = session.query(User)
     sel = query.select(User.c.username.in_(user))
     if len(sel) == 0 or sel[0].password != password:
         return -1
     else:
         return sel[0].id

def user_add(session,args):
     user = User()
     # FIXME: input should be a hash, not a long list of vars
     user.id = int(time.time()) # FIXME
     user.username = args["username"]
     user.password = args["password"]
     user.first = args["first"]
     user.middle = args["middle"]
     user.last = args["last"]
     user.description = args["description"]
     user.email = args["email"]
     # FIXME: we'd want to do validation here (actually in the User class) 
     session.save(user)
     return user in session

def user_delete(session,id):
     query = session.query(User)
     user = query.get_by(User.c.id.in_(id))
     if user is None:
        return False
     session.delete(user)
     return not user in session

def user_list(session):
     query = session.query(User)
     sel = query.select()
     return [x.to_datastruct() for x in sel]


def register_rpc(handlers):
     handlers["user_login"]  = user_login
     handlers["user_add"]    = user_add
     handlers["user_delete"] = user_delete
     handlers["user_list"]   = user_list

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

