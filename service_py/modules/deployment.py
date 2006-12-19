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
import baseobj
import traceback
import threading

import machine
import image

#---------------------------------------------------------

class Deployment(baseobj.BaseObject):

    def _produce(klass, deployment_dep_args,operation=None):
        """
        Factory method.  Create a deployment object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the deployment object.
        """

        self = Deployment()
        self.from_datastruct(deployment_dep_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,deployment_dep_args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the deployment as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        deployment object for interaction with the ORM.  See methods below for examples.
        """

        self.id            = self.load(deployment_dep_args,"id")
        self.machine_id    = self.load(deployment_dep_args,"machine_id")
        self.image_id      = self.load(deployment_dep_args,"image_id")
        self.state         = self.load(deployment_dep_args,"state")

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return {
            "id"           : self.id,
            "machine_id"   : self.machine_id,
            "image_id"     : self.image_id,
            "state"        : self.state,
        }

    def validate(self,operation):
 
        invalid = {}
        passed = True

        if operation in [OP_EDIT]:
            if self.machine_id is None:
                passed = False
                invalid["machine_id"] = REASON_REQUIRED
            if self.image_id is None:
                passed = False
                invalid["image_id"] = REASON_REQUIRED

        # FIXME: reduce boilerplate in doing things like this...
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            try:
                self.id = int(self.id)
            except:
                passed = False
                invalid["id"] = REASON_TYPE
        
        # TODO: state is in one of the valid states

        if not passed:
            raise InvalidArgumentsException(invalid_fields=invalid)


#---------------------------------------------------------

def deployment_add(websvc,deployment_dep_args):
     """
     Create a deployment.  deployment_dep_args should contain all fields except ID.
     """

     u = Deployment.produce(deployment_dep_args,OP_ADD)

     st = """
     INSERT INTO deployments (machine_id,image_id,state)
     VALUES (:machine_id,:image_id,:state)
     """

     fields = {}

     try:
         machine.machine_get(websvc, { "id" : deployment_dep_args["machine_id"]})
     except ShadowManagerException:
         raise OrphanedObjectException(invalid_fields={'machine_id':REASON_ID})

     try:
         image.image_get(websvc, { "id" : deployment_dep_args["image_id"]})
     except ShadowManagerException:
         raise OrphanedObjectException(invalid_fields={'image_id':REASON_ID})

     lock = threading.Lock()
     lock.acquire()

     try:
         websvc.cursor.execute(st, u.to_datastruct())
         websvc.connection.commit()
     except Exception:
         lock.release()
         # FIXME: be more fined grained (find where IntegrityError is defined)
         raise SQLException(traceback=traceback.format_exc())

     rowid = websvc.cursor.lastrowid
     lock.release()

     return success(rowid)

#---------------------------------------------------------

def deployment_edit(websvc,deployment_dep_args):
     """
     Edit a deployment.  deployment_dep_args should contain all fields that need to
     be changed.
     """

     u = Deployment.produce(deployment_dep_args,OP_EDIT) # force validation

     st = """
     UPDATE deployments 
     SET machine_id=:machine_id, state=:state
     WHERE id=:id
     """

     try:
         machine.machine_get(websvc, { "id" : u.machine_id })
     except ShadowManagerException:
         raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

     try:
         image.image_get(websvc, { "id" : u.image_id })
     except ShadowManagerException:
         raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()

     return success(u.to_datastruct(True))

#---------------------------------------------------------

def deployment_delete(websvc,deployment_dep_args):
     """
     Deletes a deployment.  The deployment_dep_args must only contain the id field.
     """
     u = Deployment.produce(deployment_dep_args,OP_DELETE) # force validation
 
     st = """
     DELETE FROM deployments WHERE deployments.id=:id
     """

     # check to see that what we are deleting exists
     rc = deployment_get(websvc,deployment_dep_args)
     if not rc:
        raise NoSuchObjectException()

     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()

     # FIXME: failure based on existance
     return success()

#---------------------------------------------------------

def deployment_list(websvc,deployment_dep_args):
     """
     Return a list of deployments.  The deployment_dep_args list is currently *NOT*
     used.  Ideally we need to include LIMIT information here for
     GUI pagination when we start worrying about hundreds of systems.
     """

     offset = 0
     limit  = 100
     if deployment_dep_args.has_key("offset"):
        offset = deployment_dep_args["offset"]
     if deployment_dep_args.has_key("limit"):
        limit = deployment_dep_args["limit"]

     st = """
     SELECT 
     deployments.id,
     deployments.machine_id,
     deployments.image_id,
     deployments.state,
     images.id,
     images.name,
     images.version,
     images.filename,
     images.specfile,
     images.distribution_id,
     images.virt_storage_size,
     images.virt_ram,
     images.kickstart_metadata,
     images.kernel_options,
     images.valid_targets,
     images.is_container,
     machines.id,
     machines.address, 
     machines.architecture,
     machines.processor_speed,
     machines.processor_count,
     machines.memory,
     machines.kernel_options,
     machines.kickstart_metadata,
     machines.list_group,
     machines.mac_address,
     machines.is_container,
     machines.image_id
     FROM deployments,images,machines 
     WHERE images.id = deployments.image_id AND
     machines.id = deployments.machine_id
     LIMIT ?,?
     """ 

     results = websvc.cursor.execute(st, (offset,limit))
     results = websvc.cursor.fetchall()
     if results is None:
         return success([])

     deployments = []

     for x in results:

         image_data = image.Image.produce({
                "id"                 : x[4],
                "name"               : x[5],
                "version"            : x[6],
                "filename"           : x[7],
                "specfile"           : x[8],
                "distribtuion_id"    : x[9],
                "virt_storage_size"  : x[10],
                "virt_ram"           : x[11],
                "kickstart_metadata" : x[12],
                "kernel_options"     : x[13],
                "valid_targets"      : x[14],
                "is_container"       : x[15]
         }).to_datastruct(True)

         machine_data = machine.Machine.produce({
                "id"                 : x[16],
                "address"            : x[17],
                "architecture"       : x[18],
                "processor_speed"    : x[19],
                "processor_count"    : x[20],
                "memory"             : x[21],
                "kernel_options"     : x[22],
                "kickstart_metadata" : x[23],
                "list_group"         : x[24],
                "mac_address"        : x[25],
                "is_container"       : x[26],
                "image_id"           : x[27]
         }).to_datastruct(True)

         data = Deployment.produce({         
            "id"           : x[0],
            "machine_id"   : x[1],
            "image_id"     : x[2],
            "state"        : x[3],
         }).to_datastruct(True)

         data["image"] = image_data
         data["machine"] = machine_data
         deployments.append(data)

     return success(deployments)

#---------------------------------------------------------

def deployment_get(websvc,deployment_dep_args):
     """
     Return a specific deployment record.  Only the "id" is required in deployment_dep_args.
     """

     u = Deployment.produce(deployment_dep_args,OP_GET) # force validation

     st = """
     SELECT deployments.id,deployments.machine_id,deployments.image_id,deployments.state,
     images.id, machines.id
     FROM deployments,images,machines WHERE deployments.id=:id AND 
     images.id = deployments.image_id AND machines.id = deployments.machine_id
     """

     websvc.cursor.execute(st,{ "id" : u.id })
     x = websvc.cursor.fetchone()
     if x is None:
         raise NoSuchObjectException()

     # exceptions will be raised by these next two calls, so no RC
     # checking is required
     machine_results = machine.machine_get(websvc, { "id" : x[1] })
     image_results   = image.image_get(websvc, { "id" : x[2] })

     data = Deployment.produce({
            "id"         : x[0],
            "machine_id" : x[1],
            "image_id"   : x[2],
            "state"      : x[3],
     }).to_datastruct(True)

     data["machine"] = machine_results.data
     data["image"]   = image_results.data

     return success(data)

#---------------------------------------------------------

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """
     handlers["deployment_add"]    = deployment_add
     handlers["deployment_delete"] = deployment_delete
     handlers["deployment_list"]   = deployment_list
     handlers["deployment_get"]    = deployment_get
     handlers["deployment_edit"]   = deployment_edit

