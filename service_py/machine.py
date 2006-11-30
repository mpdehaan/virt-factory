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


from codes import *
from errors import *
import baseobj
import traceback
import threading
import distribution
import provisioning

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

        self.id               = self.load(args,"id")
        self.address          = self.load(args,"address")
        self.architecture     = self.load(args,"architecture")
        self.processor_speed  = self.load(args,"processor_speed")
        self.processor_count  = self.load(args,"processor_count")
        self.memory           = self.load(args,"memory")
        self.distribution_id  = self.load(args,"distribution_id")
        self.kernel_options   = self.load(args,"kernel_options")
        self.kickstart_metadata = self.load(args, "kickstart_metadata")
        self.list_group         = self.load(args, "list_group")

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return {
            "id"                 : self.id,
            "address"            : self.address,
            "architecture"       : self.architecture,
            "processor_speed"    : self.processor_speed,
            "processor_count"    : self.processor_count,
            "memory"             : self.memory,
            "distribution_id"    : self.distribution_id,
            "kernel_options"     : self.kernel_options,
            "kickstart_metadata" : self.kickstart_metadata,
            "list_group"         : self.list_group
        }

    def validate(self,operation):
        # FIXME
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def machine_add(websvc,args):
     """
     Create a machine.  args should contain all fields except ID.
     """

     u = Machine.produce(args,OP_ADD)

     st = """
     INSERT INTO machines (address,architecture,processor_speed,
     processor_count,memory,distribution_id,
     kernel_options,kickstart_metadata,list_group)
     VALUES (:address,:architecture,:processor_speed,
     :processor_count,:memory,:distribution_id, 
     :kernel_options, :kickstart_metadata, :list_group)
     """

     u = Machine.produce(args,OP_ADD)
     if u.distribution_id is not None:
         try:
             obj = distribution.distribution_get(websvc, { "id" : u.distribution_id })
         except ShadowManagerException:
             raise OrphanedObjectException("distribution_id")

     lock = threading.Lock()
     lock.acquire()

     try:
         websvc.cursor.execute(st, u.to_datastruct())
         websvc.connection.commit()
     except Exception:
         # FIXME: be more fined grained (IntegrityError only)
         lock.release()
         raise SQLException(traceback.format_exc())

     id = websvc.cursor.lastrowid
     lock.release() 

     provisioning.provisioning_sync(websvc, {})

     return success(id)

def machine_edit(websvc,args):
     """
     Edit a machine.
     """

     u = Machine.produce(args,OP_EDIT) # force validation

     st = """
     UPDATE machines 
     SET address=:address,
     architecture=:architecture,
     processor_speed=:processor_speed,
     processor_count=:processor_count,
     memory=:memory,
     kernel_options=:kernel_options,
     kickstart_metadata=:kickstart_metadata,
     list_group=:list_group
     WHERE id=:id
     """

     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()

     provisioning.provisioning_sync(websvc,{})

     return success(u.to_datastruct(True))

def machine_delete(websvc,args):
     """
     Deletes a machine.  The args must only contain the id field.
     """

     u = Machine.produce(args,OP_DELETE) # force validation

     st = """
     DELETE FROM machines WHERE machines.id=:id
     """

     st2 = """
     SELECT machines.id FROM deployments,machines where deployments.machine_id = machines.id
     AND machines.id=:id
     """
     # check to see that what we are deleting exists
     rc = machine_get(websvc,args)
     if not rc:
        raise NoSuchObjectException("machine_delete")

     websvc.cursor.execute(st2, { "id" : u.id })
     results = websvc.cursor.fetchall()
     if results is not None and len(results) != 0:
        raise OrphanedObjectException("deployment")

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
     SELECT machines.id AS mid, machines.address,machines.architecture,
     machines.processor_speed,machines.processor_count,machines.memory,
     distributions.id AS did, machines.kernel_options,machines.kickstart_metadata,
     machines.list_group, distributions.kernel, distributions.initrd,
     distributions.options, distributions.kickstart, distributions.name
     FROM machines
     LEFT OUTER JOIN distributions ON machines.distribution_id = distributions.id  
     LIMIT ?,?
     """ 

     results = websvc.cursor.execute(st, (offset,limit))
     results = websvc.cursor.fetchall()

     if results is None:
         return success([])

     machines = []
     for x in results:

         data = Machine.produce({         
             "id"                 : x[0],
             "address"            : x[1],
             "architecture"       : x[2],
             "processor_speed"    : x[3],
             "processor_count"    : x[4],
             "memory"             : x[5],
             "distribution_id"    : x[6],
             "kernel_options"     : x[7],
             "kickstart_metadata" : x[8],
             "list_group"         : x[9]
         }).to_datastruct(True)

         if x[6] is not None and x[6] != -1:
             data["distribution"] = distribution.Distribution.produce({
                 "id"             : x[6],
                 "kernel"         : x[10],
                 "initrd"         : x[11],
                 "options"        : x[12],
                 "kickstart"      : x[13],
                 "name"           : x[14]
             }).to_datastruct(True)
     
         machines.append(data)

     return success(machines)

def machine_get(websvc,args):
     """
     Return a specific machine record.  Only the "id" is required in args.
     """

     u = Machine.produce(args,OP_GET) # force validation

     st = """
     SELECT id,address,architecture,processor_speed,processor_count,memory,
     distribution_id, kernel_options, kickstart_metadata, list_group
     FROM machines WHERE id=:id
     """
     websvc.cursor.execute(st,u.to_datastruct())
     x = websvc.cursor.fetchone()
     if x is None:
         raise NoSuchObjectException("machine_get")

     data = {
            "id"              : x[0],
            "address"         : x[1],
            "architecture"    : x[2],
            "processor_speed" : x[3],
            "processor_count" : x[4],
            "memory"          : x[5],
            "distribution_id" : x[6],
            "kernel_options"  : x[7],
            "kickstart_metadata" : x[8],
            "list_group"         : x[9],
     }

     data = Machine.produce(data).to_datastruct(True)

     if x[6] is not None and x[6] != -1:
         (rc, dist) = distribution.distribution_get(websvc, {"id":x[6]})
         if rc != 0:
             raise OrphanedObjectException("distribution_id")
         data["distribution"] = dist

     return success(data)

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """

     handlers["machine_add"]    = machine_add
     handlers["machine_delete"] = machine_delete
     handlers["machine_list"]   = machine_list
     handlers["machine_get"]    = machine_get
     handlers["machine_edit"]   = machine_edit

