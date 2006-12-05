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


import base64
from codes import *
from errors import *
import baseobj
import traceback
import threading

class User(baseobj.BaseObject):

    def _produce(klass, args,operation=None):
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
        self.id          = self.load(args,"id")
        self.username    = self.load(args,"username")
        self.password    = self.load(args,"password")
        self.first       = self.load(args,"first")
        self.middle      = self.load(args,"middle")
        self.last        = self.load(args,"last")
        self.description = self.load(args,"description")
        self.email       = self.load(args,"email")

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """
        return {
            "id"          : self.id,
            "username"    : self.username,
            "password"    : self.password,
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

        Note that getting python exception errors during a cast here is technically good enough
        to prevent GIGO, but really InvalidArgumentsExceptions should be raised.  That's what
        we want.

        NOTE: API currently gives names of invalid fields but does not list reasons.  
        i.e. (FALSE, INVALID_ARGUMENTS, ["foo,"bar"].  By making the 3rd argument a hash
        it could, but these would also need to be codes.  { "foo" : OUT_OF_RANGE, "bar" : ... }
        Up for consideration, but probably not needed at this point.  Can be added later. 
        """
        # FIXME: validation thoughts: (more can be added later)
        #  check for duplicate usernames (but maybe in "add" instead)
        #  don't delete the admin user (also maybe in the "delete" method)
        #  email regex check (tricky, RFC modules only if available, don't do it ourselves)
        #  certain fields required to *not* be blank in certain cases?
        #  username is printable
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def user_login(websvc,username,password):
     """
     Try to log in user with (user,password) and return a token, or raise
     UserInvalidException or PasswordInvalidException on error.
     """
     # this method is the exception to the rule and doesn't do object validation.
     # login is the only special method like this in the whole API.  It's also
     # the only method that doesn't take a hash for a parameter, though this
     # should probably change for consistancy.
     st = """
     SELECT id, password FROM users WHERE username=:username
     """

     if not os.path.exists("/var/lib/shadowmanager/settings"):
         # the app isn't configured.  What this means is that there are (at minimum) no
         # distributions configured and it's basically unusuable.  The WUI here should
         # show a simple splash screen saying the service isn't configured and that the
         # user needs to run two steps on the server.  "shadow init" to create the
         # default config and "shadow import" to import distributions.  Once this is done
         # they will be able to reload and use the WUI,
         raise MisconfiguredException("/var/lib/shadowmanager/settings doesn't exist")

     websvc.cursor.execute(st, { "username" : username })
     results = websvc.cursor.fetchone()
     if results is None:
         raise UserInvalidException()
     elif results[1] != password:
         raise PasswordInvalidException()
     else:
         urandom = open("/dev/urandom")
         token = base64.b64encode(urandom.read(100)) 
         urandom.close()
         return success(token)

def user_add(websvc,args):
     """
     Create a user.  args should contain all user fields except ID.
     """
     u = User.produce(args,OP_ADD)
     # u.id = websvc.get_uid()
     st = """
     INSERT INTO users (username,password,first,middle,last,description,email)
     VALUES (:username,:password,:first,:middle,:last,:description,:email)
     """
     lock = threading.Lock()
     lock.acquire()
     try:
         websvc.cursor.execute(st, u.to_datastruct())
         websvc.connection.commit()
     except Exception:
         lock.release()
         raise SQLException(traceback.format_exc())
     id = websvc.cursor.lastrowid
     lock.release()
     return success(id)

def user_edit(websvc,args):
     """
     Edit a user.  args should contain all user fields that need to
     be changed.
     """
     # FIXME: allow the password field to NOT be sent, therefore not
     #        changing it.  (OR) just always do XMLRPC/HTTPS and use a 
     #        HTML password field.  Either way.  (We're going to be
     #        wanting HTTPS anyhow).
     u = User.produce(args,OP_EDIT) # force validation
     st = """
     UPDATE users
     SET password=:password,
     first=:first,
     middle=:middle,
     last=:last,
     description=:description,
     email=:email
     WHERE id=:id
     """
     ds = u.to_datastruct()
     websvc.cursor.execute(st, ds)
     websvc.connection.commit()
     return success(u.to_datastruct())

# FIXME: don't allow delete if only 1 user left.
# FIXME: consider an undeletable but modifiable admin user

def user_delete(websvc,args):
     """
     Deletes a user.  The args must only contain the id field.
     """
     u = User.produce(args,OP_DELETE) # force validation
     st = """
     DELETE FROM users WHERE users.id=:id
     """
     websvc.cursor.execute(st, { "id" : u.id })
     websvc.connection.commit()
     # FIXME: failure based on existance
     return success()

def user_list(websvc,args):
     """
     Return a list of users.  The args list is currently *NOT*
     used.  Ideally we need to include LIMIT information here for
     GUI pagination when we start worrying about hundreds of systems.
     """
     # FIXME: limit query support
     offset = 0
     limit  = 100
     if args.has_key("offset"):
        offset = args["offset"]
     if args.has_key("limit"):
        limit = args["limit"]
     st = """
     SELECT id,username,password,first,middle,last,description,email FROM users LIMIT ?,?
     """ 
     results = websvc.cursor.execute(st, (offset,limit))
     results = websvc.cursor.fetchall()
     users = []
     for x in results:
         data = {         
            "id"          : x[0],
            "username"    : x[1],
            "password"    : x[2],
            "first"       : x[3],
            "middle"      : x[4],
            "last"        : x[5],
            "description" : x[6],
            "email"       : x[7]
         }
         users.append(User.produce(data).to_datastruct(True))
     return success(users)

def user_get(websvc,args):
     """
     Return a specific user record.  Only the "id" is required in args.
     """
     u = User.produce(args,OP_GET) # force validation
     st = """
     SELECT id,username,password,first,middle,last,description,email from users where users.id=:id
     """
     websvc.cursor.execute(st,{ "id" : u.id })
     x = websvc.cursor.fetchone()
     if x is None:
         raise NoSuchObjectException("user_get")
     data = {
            "id"          : x[0],
            "username"    : x[1],
            "password"    : x[2],
            "first"       : x[3],
            "middle"      : x[4],
            "last"        : x[5],
            "description" : x[6],
            "email"       : x[7]
     }
     return success(User.produce(data).to_datastruct(True))

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

