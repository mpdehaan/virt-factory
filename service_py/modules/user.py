#!/usr/bin/python

## ShadowManager backend code.
##
## Copyright 2006, Red Hat, Inc
## Michael DeHaan <mdehaan@redhat.com>
## Scott Seago <sseago@redhat.com>
## Adrian Likins <alikins@redhat.com>
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.



from codes import *
import baseobj

import web_svc

import os
import base64
import threading
import traceback

class UserData(baseobj.BaseObject):
    def _produce(klass, user_args,operation=None):
        """
        Factory method.  Create a user object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the user object.
        """ 
        self = UserData()
        self.from_datastruct(user_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,user_args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the user as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        user object for interaction with the ORM.  See methods below for examples.
        """ #"
        self.id          = self.load(user_args,"id")
        self.username    = self.load(user_args,"username")
        self.password    = self.load(user_args,"password")
        self.first       = self.load(user_args,"first")
        self.middle      = self.load(user_args,"middle")
        self.last        = self.load(user_args,"last")
        self.description = self.load(user_args,"description")
        self.email       = self.load(user_args,"email")

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
        """ #"
        
        # FIXME: validation thoughts: (more can be added later)
        #  check for duplicate usernames (but maybe in "add" instead)
        #  don't delete the admin user (also maybe in the "delete" method)
        #  email regex check (tricky, RFC modules only if available, don't do it ourselves)
        #  certain fields required to *not* be blank in certain cases?
        #  username is printable
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

class User(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"user_login": self.login,
                        "user_add": self.add,
                        "user_edit": self.edit,
                        "user_delete": self.delete,
                        "user_list": self.list,
                        "user_get": self.get}
        web_svc.AuthWebSvc.__init__(self)

    def login(self, username, password):
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
             raise MisconfiguredException(comment="/var/lib/shadowmanager/settings doesn't exist")

         self.cursor.execute(st, { "username" : username })
         results = self.cursor.fetchone()
         if results is None:
             raise UserInvalidException(comment=username)
         elif results[1] != password:
             raise PasswordInvalidException(comment=username)
         else:
             urandom = open("/dev/urandom")
             token = base64.b64encode(urandom.read(100)) 
             urandom.close()

         print "token", token
         return success(data=token)

    def add(self, user_args):
         """
         Create a user.  user_args should contain all user fields except ID.
         """
         u = UserData.produce(user_args,OP_ADD)
         # u.id = websvc.get_uid()
         st = """
         INSERT INTO users (username,password,first,middle,last,description,email)
         VALUES (:username,:password,:first,:middle,:last,:description,:email)
         """
         lock = threading.Lock()
         lock.acquire()
         try:
             self.cursor.execute(st, u.to_datastruct())
             self.connection.commit()
         except Exception:
             lock.release()
             raise SQLException(traceback=traceback.format_exc())
         rowid = self.cursor.lastrowid
         lock.release()
         return success(rowid)

    def edit(self, user_args):
         """
         Edit a user.  user_args should contain all user fields that need to
         be changed.
         """
         # FIXME: allow the password field to NOT be sent, therefore not
         #        changing it.  (OR) just always do XMLRPC/HTTPS and use a 
         #        HTML password field.  Either way.  (We're going to be
         #        wanting HTTPS anyhow).
         u = UserData.produce(user_args,OP_EDIT) # force validation
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
         self.cursor.execute(st, ds)
         self.connection.commit()
         return success(u.to_datastruct())

     # FIXME: don't allow delete if only 1 user left
     # FIXME: consider an undeletable but modifiable admin user

    def delete(self,user_args):
         """
         Deletes a user.  The user_args must only contain the id field.
         """
         u = UserData.produce(user_args,OP_DELETE) # force validation
         st = """
         DELETE FROM users WHERE users.id=:id
         """
         self.cursor.execute(st, { "id" : u.id })
         self.connection.commit()
         # FIXME: failure based on existance
         return success()

    def list(self,user_args):
         """
         Return a list of users.  The user_args list is currently *NOT*
         used.  Ideally we need to include LIMIT information here for
         GUI pagination when we start worrying about hundreds of systems.
         """
         # FIXME: limit query support
         offset = 0
         limit  = 100
         if user_args.has_key("offset"):
            offset = user_args["offset"]
         if user_args.has_key("limit"):
            limit = user_args["limit"]
         st = """
         SELECT id,username,password,first,middle,last,description,email FROM users LIMIT ?,?
         """ 
         results = self.cursor.execute(st, (offset,limit))
         results = self.cursor.fetchall()
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
             users.append(UserData.produce(data).to_datastruct(True))
         return success(users)

    def get(self,user_args):
         """
         Return a specific user record.  Only the "id" is required in user_args.
         """
         u = UserData.produce(user_args,OP_GET) # force validation
         st = """
         SELECT id,username,password,first,middle,last,description,email from users where users.id=:id
         """
         self.cursor.execute(st,{ "id" : u.id })
         x = self.cursor.fetchone()
         if x is None:
             raise NoSuchObjectException(comment="user_get")
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
         return success(UserData.produce(data).to_datastruct(True))


methods = User()
register_rpc = methods.register_rpc

