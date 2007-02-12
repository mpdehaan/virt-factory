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
import cobbler
import provisioning
import web_svc
import regtoken

import threading
import traceback

#------------------------------------------------------

class MachineData(baseobj.BaseObject):

    FIELDS = [ "id", "hostname", "ip_address", "architecture", "processor_speed", "processor_count", "memory",
               "kernel_options", "kickstart_metadata", "list_group", "mac_address", "is_container",
               "image_id", "puppet_node_diff" ]

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
        self.hostname           = self.load( machine_args, "hostname" )
        self.ip_address         = self.load( machine_args, "ip_address" )
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
        self.puppet_node_diff   = self.load( machine_args, "puppet_node_diff" )

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return {
            "id"                 : self.id,
            "hostname"           : self.hostname,
            "ip_address"         : self.ip_address,
            "architecture"       : self.architecture,
            "processor_speed"    : self.processor_speed,
            "processor_count"    : self.processor_count,
            "memory"             : self.memory,
            "kernel_options"     : self.kernel_options,
            "kickstart_metadata" : self.kickstart_metadata,
            "list_group"         : self.list_group,
            "mac_address"        : self.mac_address,
            "is_container"       : self.is_container,
            "image_id"           : self.image_id,
            "puppet_node_diff"   : self.puppet_node_diff
        }

    def validate(self,operation):

        invalid_args = {}

        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            try:
                self.id = int(self.id)
            except:
                invalid_args["id"] = REASON_FORMAT

        if operation in [OP_ADD, OP_EDIT]:

           # architecture is one of the listed arches
           if self.architecture and not self.architecture in VALID_ARCHS:
               invalid_args["architecture"] = REASON_RANGE

           # processor speed is a positive int
           if self.processor_speed and not type(self.processor_speed) == int and self.processor_speed > 0:
               invalid_args["processor_speed"] = REASON_FORMAT

           # processor count is a positive int
           if self.processor_count and not type(self.processor_count) == int and self.processor_count > 0:
               invalid_args["processor_count"] = REASON_FORMAT

           # memory is a positive int
           if self.memory and not type(self.memory) == int and self.memory > 0:
               invalid_args["memory"] = REASON_FORMAT

           # kernel_options is printable or None
           if self.kernel_options and not self.is_printable(self.kernel_options):
               invalid_args["kernel_options"] = REASON_FORMAT
           # kickstart metadata is printable or None
           if self.kickstart_metadata and not self.is_printable(self.kickstart_metadata):
               invalid_args["kickstart_metadata"] = REASON_FORMAT
           # list group is printable or None
           if self.list_group is not None and not self.is_printable(self.list_group):
               invalid_args["list_group"] = REASON_FORMAT
           # puppet_node_diff should probably validate possible puppet classnames
           if self.puppet_node_diff is not None and not self.is_printable(self.puppet_node_diff):
               invalid_args["puppet_node_diff"] = REASON_FORMAT

        if len(invalid_args) > 0:
            
            print "invalid args"
            print invalid_args
            raise InvalidArgumentsException(invalid_fields=invalid_args)
 
#------------------------------------------------------

class Machine(web_svc.AuthWebSvc):

    add_fields = [ x for x in MachineData.FIELDS ]
    add_fields.remove("id")
    edit_fields = [ x for x in MachineData.FIELDS ]
    edit_fields.remove("id")

    DB_SCHEMA = {
        "table"  : "machines",
        "fields" : MachineData.FIELDS,
        "add"    : add_fields,
        "edit"   : edit_fields 
    } 

    def __init__(self):
        self.methods = {"machine_add": self.add,
                        "machine_new": self.new,
                        "machine_associate": self.associate,
                        "machine_delete": self.delete,
                        "machine_edit": self.edit,
                        "machine_list": self.list,
                        "machine_get": self.get}
        web_svc.AuthWebSvc.__init__(self)
        self.db.db_schema = self.DB_SCHEMA


    def add(self, token, args):
        """
        Create a machine.  machine_args should contain all fields except ID.
        """

        st = """
        INSERT INTO machines (
        hostname,
        ip_address,
        architecture,
        processor_speed,
        processor_count,
        memory,
        kernel_options,
        kickstart_metadata,
        list_group, 
        mac_address, 
        is_container, 
        image_id,
        puppet_node_diff) 
        VALUES (
        :hostname,
        :ip_address,
        :architecture,
        :processor_speed,
        :processor_count,
        :memory,
        :kernel_options, 
        :kickstart_metadata, 
        :list_group, 
        :mac_address, 
        :is_container, 
        :image_id,
        :puppet_node_diff)
        """

        u = MachineData.produce(args,OP_ADD)
        print "u.image_id", u.image_id
        if u.image_id is not None:
            print "creating an image.Image()" 
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

        # for a "empty" machie add, we don't need to call cobbler
        if u.image_id:
            self.cobbler_sync(u.to_datastruct())
        return success(rowid)

    def cobbler_sync(self, data):
        cobbler_api = cobbler.api.BootAPI()
        images = image.Image().list(None, {}).data
        provisioning.CobblerTranslatedSystem(cobbler_api, images, data)
 

    def new(self, token):
        """
        Allocate a new machine record to be fill in later. Return a machine_id
        """

        args = {}
        print "machine_new"
        return self.add(token, args)


    def associate(self, token, machine_id, hostname, ip_addr, mac_addr, image_id=None,
                  architecture=None, processor_speed=None, processor_count=None,
                  memory=None):
        """
        Associate a machine with an ip/host/mac address
        """
        print "associating..."
        # determine the image from the token. 
        # FIXME: inefficient. ideally we'd have a retoken.get_by_value() or equivalent
        regtoken_obj = regtoken.RegToken()
        if token is None:
            print "token is None???"
        results = regtoken_obj.get_by_token(None, { "token" : token })
        print "get_by_token"
        print "results: %s" % results
        if results.error_code != 0:
            raise codes.InvalidArgumentsException("bad token")
        # FIXME: check that at least some results are returned.

        if results.data[0].has_key("image_id"):
            image_id = results.data[0]["image_id"]


        args = {
            'id': machine_id,
            'hostname': hostname,
            'ip_address': ip_addr,
            'mac_address': mac_addr,
            'image_id': image_id,
            'architecture' : architecture,
            'processor_speed' : processor_speed,
            'processor_count' : processor_count,
            'memory' : memory
        }
        print args
        return self.edit(token, args)
        
    def edit(self, token, machine_args):
         """
         Edit a machine.
         """

         u = MachineData.produce(machine_args,OP_EDIT) # force validation

         st = """
         UPDATE machines 
         SET hostname=:hostname,
         ip_address=:ip_address,
         architecture=:architecture,
         processor_speed=:processor_speed,
         processor_count=:processor_count,
         memory=:memory,
         kernel_options=:kernel_options,
         kickstart_metadata=:kickstart_metadata,
         list_group=:list_group,
         mac_address=:mac_address,
         is_container=:is_container,
         image_id=:image_id,
         puppet_node_diff=:puppet_node_diff
         WHERE id=:id
         """

         if u.image_id is not None:
            try:
                image_obj = image.Image()
                image_obj.get(token, { "id" : u.image_id })
            except ShadowManagerException:
                raise OrphanedObjectException(comments="no image found",invalid_fields={"image_id":REASON_ID})

         self.db.cursor.execute(st, u.to_datastruct())
         self.db.connection.commit()

         if u.image_id:
             self.cobbler_sync(u.to_datastruct())

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
         # this will raise an exception if the machine isn't there. 
#        self.get(token,machine_args)

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
         machines.hostname,
         machines.ip_address,
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
         machines.puppet_node_diff,
         images.name,
         images.version,
         images.distribution_id,
         images.virt_storage_size,
         images.virt_ram,
         images.kickstart_metadata,
         images.kernel_options,
         images.valid_targets,
         images.is_container,
         images.puppet_classes
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
                 "hostname"           : x[1],
                 "ip_address"         : x[2],
                 "architecture"       : x[3],
                 "processor_speed"    : x[4],
                 "processor_count"    : x[5],
                 "memory"             : x[6],
                 "kernel_options"     : x[7],
                 "kickstart_metadata" : x[8],
                 "list_group"         : x[9],
                 "mac_address"        : x[10],
                 "is_container"       : x[11],
                 "image_id"           : x[12],
                 "puppet_node_diff"   : x[13]
             }).to_datastruct(True)

             if x[12] is not None and x[12] != -1:
                 data["image"] = image.ImageData.produce({
                      "id"                 : x[12],
                      "name"               : x[14],
                      "version"            : x[15],
                      "distribution_id"    : x[16],
                      "virt_storage_size"  : x[17],
                      "virt_ram"           : x[18],
                      "kickstart_metadata" : x[19],
                      "kernel_options"     : x[20],
                      "valid_targets"      : x[21],
                      "is_container"       : x[22],
                      "puppet_classes"     : x[23]
                 }).to_datastruct(True)

             machines.append(data)

         return success(machines)


    def get(self, token, machine_args):
         """
         Return a specific machine record.  Only the "id" is required in machine_args.
         """

         u = MachineData.produce(machine_args,OP_GET) # force validation

         st = """
         SELECT id,hostname,ip_address,architecture,processor_speed,processor_count,memory,
         kernel_options, kickstart_metadata, list_group, mac_address, is_container, image_id,
         puppet_node_diff
         FROM machines WHERE id=:id
         """
         self.db.cursor.execute(st,u.to_datastruct())
         x = self.db.cursor.fetchone()
         if x is None:
             raise NoSuchObjectException(comment="machine_get")

         data = {
                "id"                 : x[0],
                "hostname"           : x[1],
                "ip_address"         : x[2],
                "architecture"       : x[3],
                "processor_speed"    : x[4],
                "processor_count"    : x[5],
                "memory"             : x[6],
                "kernel_options"     : x[7],
                "kickstart_metadata" : x[8],
                "list_group"         : x[9],
                "mac_address"        : x[10],
                "is_container"       : x[11],
                "image_id"           : x[12],
                "puppet_node_diff"   : x[13]
         }

         filtered = MachineData.produce(data).to_datastruct(True)

         # FIXME: redo this with image id

         if x[12] is not None and x[12] != -1:
             image_obj = image.Image()
             image_results = image_obj.get(token, {"id":x[12]})
             if not image_results.ok():
                 raise OrphanedObjectException(comment="image_id")
             filtered["image"] = image_results.data

         return success(filtered)


methods = Machine()
register_rpc = methods.register_rpc

