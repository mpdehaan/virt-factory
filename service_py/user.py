import time
import base64
from sqlalchemy import *
from codes import *
from errors import *
import baseobj

class User(baseobj.BaseObject):

    def _produce(clss, args,operation=None):
        self = User()
        self.from_datastruct(args)
        self.validate()
        return self
    produce = classmethod(_produce)

    def from_datastruct(self,args):
        self.id          = self.load(args,"id",-1)
        self.username    = self.load(args,"username",-1)
        self.first       = self.load(args,"first",-1)
        self.middle      = self.load(args,"middle",-1)
        self.last        = self.load(args,"last",-1)
        self.description = self.load(args,"description",-1)
        self.email       = self.load(args,"email",-1)

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

    def validate(self):
        self.id = int(self.id)


def make_table(meta):
     tbl = Table('users', meta, autoload=True)
     mapper(User, tbl)
     return tbl
   
def user_login(session,user,password):
     # this method is the exception to the rule and doesn't do object validation.
     # login is the only special method like this in the whole API.  It's also
     # the only method that doesn't take a hash for a parameter, though this
     # should probably change for consistancy.
     query = session.query(User)
     sel = query.select(User.c.username.in_(user))
     if len(sel) == 0:
         raise UserInvalidException()
     elif sel[0].password != password:
         raise PasswordInvalidException()
     else:
         urandom = open("/dev/urandom")
         token = base64.b64encode(urandom.read(100)) 
         urandom.close()
         return success(token)

def user_add(session,args):
     user = User.produce(args,OP_ADD) # force validation
     user.id = int(time.time()) # FIXME (?)
     return user_save(session,user,args)

def user_edit(session,args):
     temp_user = User.produce(args,OP_EDIT) # force validation
     query = session.query(User)
     user = query.get_by(User.c.id.in_(temp_user.id))
     if user is None:
        raise NoSuchObjectException()
     return user_save(session,user,args)

def user_save(session,user,args):
     # validation already done in methods calling this helper
     user.username = args["username"]
     user.password = args["password"]
     user.first = args["first"]
     user.middle = args["middle"]
     user.last = args["last"]
     user.description = args["description"]
     user.email = args["email"]
     # FIXME: we'd want to do validation here (actually in the User class) 
     session.save(user)
     session.flush()
     ok = user in session
     if not ok:
         raise InternalErrorException()
     return success()

# FIXME: don't allow delete if only 1 user left.
# FIXME: consider an undeletable but modifiable admin user

def user_delete(session,args):
     temp_user = User.produce(args,OP_DELETE) # force validation
     query = session.query(User)
     user = query.get_by(User.c.id.in_(temp_user.id))
     if user is None:
        return result(ERR_NO_SO_OBJECT)
     session.delete(user)
     session.flush()
     ok = not user in session
     if not ok:
         raise InternalErrorException()
     return success()

def user_list(session,args):
     # no validation required
     query = session.query(User)
     sel = query.select()
     list = [x.to_datastruct() for x in sel]
     return success(list)

def user_get(session,args):
     temp_user = User.produce(args,OP_GET) # force validation
     query = session.query(User)
     user = query.get_by(User.c.id.in_(temp_user.id))
     if user is None:
        raise NoSuchObjectException()
     return success(user.to_datastruct())

def register_rpc(handlers):
     handlers["user_login"]  = user_login
     handlers["user_add"]    = user_add
     handlers["user_delete"] = user_delete
     handlers["user_list"]   = user_list
     handlers["user_get"]    = user_get
     handlers["user_edit"]   = user_edit

