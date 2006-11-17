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

class Machine(baseobj.BaseObject):

    def _produce(klass, args,operation=None):
        """
        Factory method.  Create a machine object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the machine object.
        """
        self = Machine()
        self.from_datastruct(args)
        self.validate(operation)
        return self
    produce = classmethod(_produce)

    def from_datastruct(self,args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the machine as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        machine object for interaction with the ORM.  See methods below for examples.
        """
        self.id               = self.load(args,"id",-1)
        self.address          = self.load(args,"address",-1)
        self.architecture     = self.load(args,"architecture",-1)
        self.processor_speed  = self.load(args,"processor_speed",-1)
        self.processor_count  = self.load(args,"processor_count",-1)
        self.memory           = self.load(args,"memory",-1)

    def to_datastruct(self):
        """
        Serialize the object for transmission over WS.
        """
        return {
            "id"              : self.id,
            "address"         : self.address,
            "architecture"    : self.architecture,
            "processor_speed" : self.processor_speed,
            "processor_count" : self.processor_count,
            "memory"          : self.memory,
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

def machine_add(websvc,args):
     """
     Create a machine.  args should contain all fields except ID.
     """
     u = Machine.produce(args,OP_ADD)
     u.id = int(time.time())
     st = """
     INSERT INTO machines (id,address,architecture,processor_speed,processor_count,memory)
     VALUES (:id,:address,:architecture,:processor_speed,:processor_count,:memory)
     """
     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()
     return success(u.id)

def machine_edit(websvc,args):
     """
     Edit a machine.  args should contain all fields that need to
     be changed.
     """
     u = Machine.produce(args,OP_EDIT) # force validation
     st = """
     UPDATE machines 
     SET machines.address=:address,
     machines.architecture=:architecture,
     machines.processor_speed=:processor_speed,
     machines.processor_count=:processor_count,
     machines.memory=:memory
     WHERE machines.id=:id
     """
     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()
     return success(u.to_datastruct())

def machine_delete(websvc,args):
     """
     Deletes a machine.  The args must only contain the id field.
     """
     u = Machine.produce(args,OP_DELETE) # force validation
     st = """
     DELETE FROM machines WHERE users.id=:id
     """
     websvc.cursor.execute(st, { "id" : u.id })
     websvc.connection.commit()
     # FIXME: failure based on existance
     return success()

def machine_list(websvc,args):
     """
     Return a list of machines.  The args list is currently *NOT*
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
     SELECT id,address,architecture,processor_speed,processor_count,memory
     FROM users LIMIT ?,?
     """ 
     results = websvc.cursor.execute(st, (offset,limit))
     results = websvc.cursor.fetchall()
     machines = []
     for x in results:
         data = {         
            "id"               : x[0],
            "address"          : x[1],
            "architecture"     : x[2],
            "processor_speed"  : x[3],
            "processor_count"  : x[4],
            "memory"           : x[5],
         }
         machines.append(Machine.produce(data).to_datastruct())
     return success(machines)

def machine_get(websvc,args):
     """
     Return a specific machine record.  Only the "id" is required in args.
     """
     u = Machine.produce(args,OP_GET) # force validation
     st = """
     SELECT id,address,architecture,processor_speed,processor_count,memory
     FROM machines WHERE id=?
     """
     websvc.cursor.execute(st,{ "id" : u.id })
     x = websvc.cursor.fetchone()
     data = {
            "id"              : x[0],
            "address"         : x[1],
            "architecture"    : x[2],
            "processor_speed" : x[3],
            "processor_count" : x[4],
            "memory"          : x[5],
     }
     return success(Machine.produce(data).to_datastruct())

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """
     handlers["machine_add"]    = machine_add
     handlers["machine_delete"] = machine_delete
     handlers["machine_list"]   = machine_list
     handlers["machine_get"]    = machine_get
     handlers["machine_edit"]   = machine_edit

