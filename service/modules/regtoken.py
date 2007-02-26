"""
ShadowManager backend code.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import baseobj
from codes import *

import profile
import web_svc

import os
import threading
import traceback
import base64

#------------------------------------------------------

class RegTokenData(baseobj.BaseObject):

    FIELDS = [ "id", "token", "profile_id", "uses_remaining"] 

    def _produce(klass, args,operation=None):
        """
        Factory method.  Create a profile object from input, optionally
        running it through validation, which will vary depending on what
        operation is creating the profile object.
        """

        self = RegTokenData()
        self.from_datastruct(args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,args):
        """
        Helper method to fill in the object's internal variables from
        a hash. 
        """

        self.id                 = self.load(args,"id")
        self.token              = self.load(args,"token")
        self.profile_id           = self.load(args,"profile_id")
        self.uses_remaining     = self.load(args,"uses_remaining")

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return {
            "id"                 : self.id,
            "token"              : self.token,
            "profile_id"           : self.profile_id,
            "uses_remaining"     : self.uses_remaining,
        }

    def validate(self,operation):
        """
        Cast variables appropriately and raise InvalidArgumentException
        where appropriate.
        """
        invalid_fields = {}
        
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            try:
                self.id = int(self.id)
            except:
                invalid_fields["id"] = REASON_FORMAT
 
        if operation in [OP_ADD, OP_EDIT]:
            # uses remaining is None (infinite) or a positive integer
            if not self.uses_remaining is None:
                if type(self.uses_remaining) != int:
                    invalid_fields["uses_remaining"] = REASON_FORMAT
                elif self.uses_remaining <= 0:
                    invalid_fields["uses_remaining"] = REASON_FORMAT

        if len(invalid_fields) > 0:
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


class RegToken(web_svc.AuthWebSvc):

    DB_SCHEMA = {
        "table" : "regtokens",
        "fields" : RegTokenData.FIELDS,
        "add"   : [ "id", "token", "profile_id", "uses_remaining" ],
        "edit"  : [ "profile_id", "uses_remaining" ]
    }

    def __init__(self):
        self.methods = {
             "regtoken_add": self.add,
             "regtoken_delete": self.delete,
             "regtoken_get": self.get,
             "regtoken_get_by_token": self.get_by_token,
             "regtoken_list": self.list
        }
        web_svc.AuthWebSvc.__init__(self)
        self.db.db_schema = self.DB_SCHEMA

    def generate(self, token):
         """
         token is base64 encoded short string from /dev/urandom
         """
         fd = open("/dev/urandom")
         data = fd.read(20)
         fd.close()
         data = base64.b64encode(data)
         data = data.replace("=","")
         return data.upper() 

    def add(self, token, args):
         """
         Create a registration token.   Only profile_id and uses_remaining are used as input.
         """
         args["token"] = self.generate(token)
       
         u = RegTokenData.produce(args,OP_ADD)
         print u.to_datastruct()

         if u.profile_id is not None:
             try:
                 self.profile_obj = profile.Profile()
                 self.profile_obj.get(token, { "id" : u.profile_id})
             except ShadowManagerException:
                 raise OrphanedObjectException(comment='profile_id',traceback=traceback.format_exc())

         return self.db.simple_insert(u.to_datastruct())

    def delete(self, token, args):
         """
         Delete.  args must only contain the id field.
         """

         u = RegTokenData.produce(args,OP_DELETE) # force validation
         return self.db.simple_delete(args)

    def get_by_token(self, token, args):
         results = self.db.simple_list({}, { "token" : args["token"]})
         print "get_by_token", results
         return results

    def list(self, token, args):
         """
         Return a list of tokens.  The args list is currently *NOT*
         used.  Ideally we need to include LIMIT information here for
         GUI pagination when we start worrying about hundreds of systems.
         """

         # FIXME: make nested lists be able to do outer joins, or else fill
         # in "EMPTY" database rows for unset profiles and make those undeleteable.

         return self.db.nested_list(
            [ profile.Profile.DB_SCHEMA ],
            args,
            { "profiles.id" : "regtokens.profile_id" }
         )

    def __decrement_uses_remaining(self, id, uses):
        """
        Decrement the uses remaining for a registration token.
        """
        st = """
        UPDATE
              regtokens
        SET
              uses_remaining=:uses
        WHERE
              id=:id
         """
        
        self.db.cursor.execute(st, {'uses':(uses-1), 'id':id})
        self.db.connection.commit()

         

    def check(self, regtoken):
        """
        Validates a regtoken as being valid. If it fails, raise an
        approriate exception.
        """

        st = """
        SELECT
              id, uses_remaining
        FROM
              regtokens
        WHERE
              token=:regtoken
        """

        self.db.cursor.execute(st, {'regtoken': regtoken})
        x = self.db.cursor.fetchone()

        if x is None:
            raise RegTokenInvalidException(comment="regtoken not found in regtoken.check")

        (id, uses) = x
        if uses == 0:
            raise RegTokenExhaustedException(comment="regtoken max uses reached")

        if uses is not None:
            self.__decrement_uses_remaining(id, uses)

        # we don't really need to check this, since failure will raise exceptions
        return True
        


    def get(self, token, args):
         """
         Return a specific record.  Only the "id" is required in args.
         """

         u = RegTokenData.produce(args,OP_GET) # force validation

         st = """
         SELECT id,token,profile_id,uses_remaining
         FROM regtokens WHERE id=:id
         """

         self.db.cursor.execute(st,{ "id" : u.id })
         x = self.db.cursor.fetchone()

         if x is None:
             raise NoSuchObjectException(comment="regtoken_get")

         data = {
                "id"                 : x[0],
                "token"              : x[1],
                "profile_id"           : x[2],
                "uses_remaining"     : x[3]
         }

         data = ProfileData.produce(data).to_datastruct(True)

         if x[2] is not None:
             profile_obj = profile.Profile()
             profile_results = profile_obj.get(None, { "id" : x[2] })
             if not profile_results.ok():
                 raise OrphanedObjectException(comment="profile_id")
             data["profile"] = profile_results.data

         return success(data)



methods = RegToken()
register_rpc = methods.register_rpc


