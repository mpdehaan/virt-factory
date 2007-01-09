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


import baseobj
from codes import *

import image
import provisioning
import web_svc

import threading
import traceback

#------------------------------------------------------

class MachineData(baseobj.BaseObject):

    def _produce(klass, machine_args,operation=None):
        """
        Factory method.  Create a machine object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the machine object.
        """

        self = MachineData()
        self.from_datastruct(machine_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,machine_args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the machine as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        machine object for interaction with the ORM.  See methods below for examples.
        """

        self.id                 = self.load( machine_args, "id" )
        self.address            = self.load( machine_args, "address" )
        self.architecture       = self.load( machine_args, "architecture" )
        self.processor_speed    = self.load( machine_args, "processor_speed" )
        self.processor_count    = self.load( machine_args, "processor_count" )
        self.memory             = self.load( machine_args, "memory" )
        self.kernel_options     = self.load( machine_args, "kernel_options" )
        self.kickstart_metadata = self.load( machine_args, "kickstart_metadata" )
        self.list_group         = self.load( machine_args, "list_group" )
        self.mac_address        = self.load( machine_args, "mac_address" )
        self.is_container       = self.load( machine_args, "is_container" )
        self.image_id           = self.load( machine_args, "image_id" )

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
            "kernel_options"     : self.kernel_options,
            "kickstart_metadata" : self.kickstart_metadata,
            "list_group"         : self.list_group,
            "mac_address"        : self.mac_address,
            "is_container"       : self.is_container,
            "image_id"           : self.image_id
        }

    def validate(self,operation):

        invalid_args = {}

        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            try:
                self.id = int(self.id)
            except:
                invalid_args["id"] = REASON_FORMAT

        if operation in [OP_ADD, OP_EDIT]:

           # address is valid (need an RFC compliant module to do this right)
           if not self.is_printable(self.address):
               invalid_args["address"] = REASON_FORMAT

           # architecture is one of the listed arches
           if not self.architecture in VALID_ARCHS:
               invalid_args["architecture"] = REASON_RANGE

           # processor speed is a positive int
           if not type(self.processor_speed) == int and self.processor_speed > 0:
               invalid_args["processor_speed"] = REASON_FORMAT

           # processor count is a positive int
           if not type(self.processor_count) == int and self.processor_count > 0:
               invalid_args["processor_count"] = REASON_FORMAT

           # memory is a positive int
           if not type(self.memory) == int and self.memory > 0:
               invalid_args["memory"] = REASON_FORMAT

           # kernel_options is printable or None
           if self.kernel_options is None and not self.is_printable(self.kernel_options):
               invalid_args["kernel_options"] = REASON_FORMAT
           # kickstart metadata is printable or None
           if self.kickstart_metadata is None and not self.is_printable(self.kickstart_metadata):
               invalid_args["kickstart_metadata"] = REASON_FORMAT
           # list group is printable or None
           if self.list_group is not None and not self.is_printable(self.list_group):
               invalid_args["list_group"] = REASON_FORMAT

        if len(invalid_args) > 0:
            print "Invalid args:", invalid_args
            
            raise InvalidArgumentsException(invalid_args=invalid_args)
 
#------------------------------------------------------

class Machine(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"machine_add": self.add,
                        "machine_delete": self.delete,
                        "machine_edit": self.edit,
                        "machine_list": self.list,
                        "machine_get": self.get}
        web_svc.AuthWebSvc.__init__(self)



    def add(self, token, args):
        """
        Create a machine.  machine_args should contain all fields except ID.
        """

        u = MachineData.produce(args,OP_ADD)
       
        st = """
        INSERT INTO machines (
        address,
        architecture,
        processor_speed,
        processor_count,
        memory,
        kernel_options,
        kickstart_metadata,
        list_group, 
        mac_address, 
        is_container, 
        image_id) 
        VALUES (
        :address,
        :architecture,
        :processor_speed,
        :processor_count,
        :memory,
        :kernel_options, 
        :kickstart_metadata, 
        :list_group, 
        :mac_address, 
        :is_container, 
        :image_id)
        """

        u = MachineData.produce(args,OP_ADD)
        if u.image_id is not None:
            try:
                self.image = image.Image()
                self.image.get( token, { "id" : u.image_id } )
            except ShadowManagerException:
                raise OrphanedObjectException(comment="image_id")

        lock = threading.Lock()
        lock.acquire()


        try:
            self.db.cursor.execute(st, u.to_datastruct())
            self.db.connection.commit()
        except Exception:
            # FIXME: be more fined grained (IntegrityError only)
            lock.release()
            raise SQLException(traceback=traceback.format_exc())

        rowid = self.db.cursor.lastrowid
        lock.release() 

        self.sync()

        return success(rowid)

    def sync(self):
        self.provisioning = provisioning.Provisioning()
        self.provisioning.sync( {} )
           
    def edit(self, token, machineargs):
         """
         Edit a machine.
         """

         u = MachineData.produce(machine_args,OP_EDIT) # force validation

         st = """
         UPDATE machines 
         SET address=:address,
         architecture=:architecture,
         processor_speed=:processor_speed,
         processor_count=:processor_count,
         memory=:memory,
         kernel_options=:kernel_options,
         kickstart_metadata=:kickstart_metadata,
         list_group=:list_group,
         mac_address=:mac_address,
         is_container=:is_container,
         image_id=:image_id
         WHERE id=:id
         """

         if u.image_id is not None:
            try:
                self.image.get( { "id" : u.image_id })
            except ShadowManagerException:
                raise OrphanedObjectException(comments="no image found",invalid_fields={"image_id":REASON_ID})

         self.db.cursor.execute(st, u.to_datastruct())
         self.db.connection.commit()

         self.sync( {} )

         return success(u.to_datastruct(True))


    def delete(self, token, machine_args):
         """
         Deletes a machine.  The machine_args must only contain the id field.
         """

         u = MachineData.produce(machine_args,OP_DELETE) # force validation

         st = """
         DELETE FROM machines WHERE machines.id=:id
         """

         # deployment orphan prevention
         st2 = """
         SELECT machines.id FROM deployments,machines where machines.id = deployments.image_id
         AND machines.id=:id
         """
         # check to see that what we are deleting exists
         # FIXME
#         rc = get(None,machine_args)
         if not rc:
            raise NoSuchObjectException(comment="machine_delete")

         self.db.cursor.execute(st2, { "id" : u.id })
         results = self.db.cursor.fetchall()
         if results is not None and len(results) != 0:
            raise OrphanedObjectException(comment="image")

         self.db.cursor.execute(st, { "id" : u.id })
         self.db.connection.commit()

         # FIXME: failure based on existance
         return success()


    def list(self, token, machine_args):
         """
         Return a list of machines.  The machine_args list is currently *NOT*
         used.  Ideally we need to include LIMIT information here for
         GUI pagination when we start worrying about hundreds of systems.
         """

         offset = 0
         limit  = 100
         if machine_args.has_key("offset"):
            offset = machine_args["offset"]
         if machine_args.has_key("limit"):
            limit = machine_args["limit"]

         st = """
         SELECT machines.id AS mid, 
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
         machines.image_id,
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
         images.is_container
         FROM machines
         LEFT OUTER JOIN images ON machines.image_id = images.id  
         LIMIT ?,?
         """ 

         results = self.db.cursor.execute(st, (offset,limit))
         results = self.db.cursor.fetchall()

         if results is None:
             return success([])

         machines = []
         for x in results:

             data = MachineData.produce({         
                 "id"                 : x[0],
                 "address"            : x[1],
                 "architecture"       : x[2],
                 "processor_speed"    : x[3],
                 "processor_count"    : x[4],
                 "memory"             : x[5],
                 "kernel_options"     : x[6],
                 "kickstart_metadata" : x[7],
                 "list_group"         : x[8],
                 "mac_address"        : x[9],
                 "is_container"       : x[10],
                 "image_id"           : x[11]
             }).to_datastruct(True)

             if x[6] is not None and x[6] != -1:
                 data["image"] = image.ImageData.produce({
                      "id"                 : x[11],
                      "name"               : x[12],
                      "version"            : x[13],
                      "filename"           : x[14],
                      "specfile"           : x[15],
                      "distribution_id"    : x[16],
                      "virt_storage_size"  : x[17],
                      "virt_ram"           : x[18],
                      "kickstart_metadata" : x[19],
                      "kernel_options"     : x[20],
                      "valid_targets"      : x[21],
                      "is_container"       : x[22]
                 }).to_datastruct(True)

             machines.append(data)

         return success(machines)


    def get(self, token, machine_args):
         """
         Return a specific machine record.  Only the "id" is required in machine_args.
         """

         u = MachineData.produce(machine_args,OP_GET) # force validation

         st = """
         SELECT id,address,architecture,processor_speed,processor_count,memory,
         kernel_options, kickstart_metadata, list_group, mac_address, is_container, image_id
         FROM machines WHERE id=:id
         """
         self.db.cursor.execute(st,u.to_datastruct())
         x = self.db.cursor.fetchone()
         if x is None:
             raise NoSuchObjectException(comment="machine_get")

         data = {
                "id"                 : x[0],
                "address"            : x[1],
                "architecture"       : x[2],
                "processor_speed"    : x[3],
                "processor_count"    : x[4],
                "memory"             : x[5],
                "kernel_options"     : x[6],
                "kickstart_metadata" : x[7],
                "list_group"         : x[8],
                "mac_address"        : x[9],
                "is_container"       : x[10],
                "image_id"           : x[11]
         }

         filtered = MachineData.produce(data).to_datastruct(True)

         # FIXME: redo this with image id

         if x[11] is not None and x[11] != -1:
             image_results = self.image.get({"id":x[11]})
             if not image_results.ok():
                 raise OrphanedObjectException(comment="image_id")
             filtered["image"] = image_results.data

         return success(filtered)


methods = Machine()
register_rpc = methods.register_rpc

