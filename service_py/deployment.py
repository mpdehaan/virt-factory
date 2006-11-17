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
from codes import *
from errors import *
import baseobj

class Deployment(baseobj.BaseObject):

    def _produce(klass, args,operation=None):
        """
        Factory method.  Create a deployment object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the deployment object.
        """
        self = Deployment()
        self.from_datastruct(args)
        self.validate(operation)
        return self
    produce = classmethod(_produce)

    def from_datastruct(self,args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the deployment as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        deployment object for interaction with the ORM.  See methods below for examples.
        """
        self.id           = self.load(args,"id",-1)
        self.machine_id   = self.load(args,"machine_id",-1)
        self.image_id     = self.load(args,"image_id",-1)
        self.state        = self.load(args,"state",-1)

    def to_datastruct(self):
        """
        Serialize the object for transmission over WS.
        """
        return {
            "id"          : self.id,
            "machine_id"  : self.machine_id,
            "image_id"    : self.image_id,
            "state"       : self.state,
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
        # FIXME
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def deployment_add(websvc,args):
     """
     Create a deployment.  args should contain all fields except ID.
     """
     u = Deployment.produce(args,OP_ADD)
     u.id = int(time.time())
     st = """
     INSERT INTO deployments (id,machine_id,image_id,state)
     VALUES (:id,:machine_id,:image_id,:state)
     """
     try:
         machine.machine_get(websvc,u.machine_id)
     except errors.ShadowManagerException:
        raise InvalidArgumentsException(["machine_id"])
     try:
        image.image_get(websvc,u.image_id)
     except errors.ShadowManagerException:
        raise InvalidArgumentsException(["image_id"])
     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()
     return success(u.id)

def deployment_edit(websvc,args):
     """
     Edit a deployment.  args should contain all fields that need to
     be changed.  For deployments, (image_id can't be changed, machine_id can)
     """
     u = Deployment.produce(args,OP_EDIT) # force validation
     st = """
     UPDATE deployments 
     SET deployments.machine_id=:machine_id,
     deployments.state=:state,
     WHERE deployments.id=:id
     """
     # FIXME: validate that machine_id and image_id are valid?
     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()
     return success(u.to_datastruct())

def deployment_delete(websvc,args):
     """
     Deletes a deployment.  The args must only contain the id field.
     """
     u = Deployment.produce(args,OP_DELETE) # force validation
     st = """
     DELETE FROM deployments WHERE users.id=:id
     """
     websvc.cursor.execute(st, { "id" : u.id })
     websvc.connection.commit()
     # FIXME: failure based on existance
     return success()

def deployment_list(websvc,args):
     """
     Return a list of deployments.  The args list is currently *NOT*
     used.  Ideally we need to include LIMIT information here for
     GUI pagination when we start worrying about hundreds of systems.
     """
     offset = 0
     limit  = 100
     if args.has_key("offset"):
        offset = args["offset"]
     if args.has_key("limit"):
        limit = args["limit"]
     st = """
     SELECT id,machine_id,image_id,state
     FROM users LIMIT ?,?
     """ 
     # FIXME: nest machine,image info
     results = websvc.cursor.execute(st, (offset,limit))
     results = websvc.cursor.fetchall()
     deployments = []
     for x in results:
         data = {         
            "id"               : x[0],
            "machine_id"       : x[1],
            "image_id"         : x[2],
            "state"            : x[3]
         }
         deployments.append(Deployment.produce(data).to_datastruct())
     return success(deployments)

def deployment_get(websvc,args):
     """
     Return a specific deployment record.  Only the "id" is required in args.
     """
     u = Deployment.produce(args,OP_GET) # force validation
     st = """
     SELECT id,machine_id,image_id,state
     FROM deployments WHERE id=?
     """
     # FIXME nest machine,image info
     websvc.cursor.execute(st,{ "id" : u.id })
     x = websvc.cursor.fetchone()
     data = {
            "id"              : x[0],
            "machine_id"      : x[1],
            "image_id"        : x[2],
            "state"           : x[3]
     }
     return success(Deployment.produce(data).to_datastruct())

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """
     handlers["deployment_add"]    = deployment_add
     handlers["deployment_delete"] = deployment_delete
     handlers["deployment_list"]   = deployment_list
     handlers["deployment_get"]    = deployment_get
     handlers["deployment_edit"]   = deployment_edit

