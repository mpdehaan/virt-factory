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


import time
import base64
from sqlalchemy import *
from codes import *
from errors import *
import baseobj

class User(baseobj.BaseObject):

    def _produce(clss, args,operation=None):
        """
        Factory method.  Create a user object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the user object.
        """
        self = User()
        self.from_datastruct(args)
        self.validate(operation)
        return self
    produce = classmethod(_produce)

    def from_datastruct(self,args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the user as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        user object for interaction with the ORM.  See methods below for examples.
        """
        self.id          = self.load(args,"id",-1)
        self.username    = self.load(args,"username",-1)
        self.first       = self.load(args,"first",-1)
        self.middle      = self.load(args,"middle",-1)
        self.last        = self.load(args,"last",-1)
        self.description = self.load(args,"description",-1)
        self.email       = self.load(args,"email",-1)

    def to_datastruct(self):
        """
        Serialize the object for transmission over WS.
        """
        return {
            "id"          : self.id,
            "username"    : self.username,
            "first"       : self.first,
            "middle"      : self.middle,
            "last"        : self.last,
            "description" : self.description,
            "email"       : self.email
        }

    def validate(self,operation):
        """
        Cast variables appropriately and raise InvalidArgumentException(["name of bad arg","..."])
        if there are any problems.  Note that validation is operation specific, for instance
        there is no ID for an "add" command because the add command generates the ID.
        """
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def make_table(meta):
     """
     This method is called to hand the table object to sqlalchemy. SQLA can actually
     create the table but for upgrade reasons, we're letting it just read the metadata.
     """
     tbl = Table('users', meta, autoload=True)
     mapper(User, tbl)
     return tbl
   
def user_login(session,user,password):
     """
     Try to log in user with (user,password) and return a token, or raise
     UserInvalidException or PasswordInvalidException on error.
     """
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
     """
     Create a user.  args should contain all user fields except ID.
     """
     user = User.produce(args,OP_ADD) # force validation
     user.id = int(time.time()) # FIXME (?)
     return user_save(session,user,args)

def user_edit(session,args):
     """
     Edit a user.  args should contain all user fields that need to
     be changed.
     """
     # FIXME: allow the password field to NOT be sent, therefore not
     #        changing it.  (OR) just always do XMLRPC/HTTPS and use a 
     #        HTML password field.  Either way.  (We're going to be
     #        wanting HTTPS anyhow).
     temp_user = User.produce(args,OP_EDIT) # force validation
     query = session.query(User)
     user = query.get_by(User.c.id.in_(temp_user.id))
     if user is None:
        raise NoSuchObjectException()
     return user_save(session,user,args)

def user_save(session,user,args):
     """
     Helper method used by user_add and user_save.
     """
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
     """
     Deletes a user.  The args must only contain the id field.
     """
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
     """
     Return a list of users.  The args list is currently *NOT*
     used.  Ideally we need to include LIMIT information here for
     GUI pagination when we start worrying about hundreds of systems.
     """
     # no validation required
     query = session.query(User)
     sel = query.select()
     list = [x.to_datastruct() for x in sel]
     return success(list)

def user_get(session,args):
     """
     Return a specific user record.  Only the "id" is required in args.
     """
     temp_user = User.produce(args,OP_GET) # force validation
     query = session.query(User)
     user = query.get_by(User.c.id.in_(temp_user.id))
     if user is None:
        raise NoSuchObjectException()
     return success(user.to_datastruct())

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """
     handlers["user_login"]  = user_login
     handlers["user_add"]    = user_add
     handlers["user_delete"] = user_delete
     handlers["user_list"]   = user_list
     handlers["user_get"]    = user_get
     handlers["user_edit"]   = user_edit

