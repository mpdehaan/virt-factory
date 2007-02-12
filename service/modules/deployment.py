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

import image
import machine
import web_svc

import traceback
import threading



#---------------------------------------------------------

class DeploymentData(baseobj.BaseObject):

    FIELDS = [ "id", "hostname", "ip_address", "mac_address", "machine_id", "image_id",
               "state", "display_name", "puppet_node_diff" ]

    def _produce(klass, deployment_dep_args,operation=None):
        """
        Factory method.  Create a deployment object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the deployment object.
        """

        self = DeploymentData()
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

        return self.deserialize(deployment_dep_args)

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return self.serialize()

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
        if operation in [OP_ADD, OP_EDIT]:
           # puppet_node_diff should probably validate possible puppet classnames
           if self.puppet_node_diff is not None and not self.is_printable(self.puppet_node_diff):
               invalid["puppet_node_diff"] = REASON_FORMAT

        if not passed:
            raise InvalidArgumentsException(invalid_fields=invalid)


class Deployment(web_svc.AuthWebSvc):

    add_fields = [ x for x in DeploymentData.FIELDS ]
    add_fields.remove("id")
    edit_fields = [ x for x in DeploymentData.FIELDS ]
    edit_fields.remove("id")
    edit_fields.remove("image_id")

    DB_SCHEMA = {
        "table"  : "deployments",
        "fields" : DeploymentData.FIELDS,
        "add"    : add_fields,
        "edit"   : edit_fields 
    } 

    def __init__(self):
        self.methods = {"deployment_add": self.add,
                        "deployment_edit": self.edit,
                        "deployment_delete": self.delete,
                        "deployment_list": self.list,
                        "deployment_get": self.get}

        web_svc.AuthWebSvc.__init__(self)
        self.db.db_schema = self.DB_SCHEMA
                        

    def add(self, token, deployment_dep_args):
         """
         Create a deployment.  deployment_dep_args should contain all fields except ID.
         """

         mac = None
         imagename = None

         try:
             machine_obj = machine.Machine()
             result = machine_obj.get(token, { "id" : deployment_dep_args["machine_id"]})
             mac = result.data["mac_address"]
         except ShadowManagerException:
             raise OrphanedObjectException(invalid_fields={'machine_id':REASON_ID})

         try:
             image_obj = image.Image()
             result = image_obj.get(token, { "id" : deployment_dep_args["image_id"]})
             imagename = result.data["name"]
         except ShadowManagerException:
             raise OrphanedObjectException(invalid_fields={'image_id':REASON_ID})

         display_name = mac + " / " + imagename

         deployment_dep_args["display_name"] = display_name
         u = DeploymentData.produce(deployment_dep_args,OP_ADD)
         return self.db.simple_add(u.to_datastruct())

    def edit(self, token, deployment_dep_args):
         """
         Edit a deployment.  deployment_dep_args should contain all fields that need to
         be changed.
         """

         try:
             machine_obj = machine.Machine()
             result = machine_obj.get(token, { "id" : deployment_dep_args["machine_id"]})
             mac = result.data["mac_address"]
         except ShadowManagerException:
             raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

         try:
             image_obj = image.Image()
             result = image_obj.get(token, { "id" : deployment_dep_args["image_id"] })
             imagename = result.data["name"]
         except ShadowManagerException:
             raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

         display_name = mac + "/" + imagename
         deployment_dep_args["display_name"] = display_name

         u = DeploymentData.produce(deployment_dep_args,OP_EDIT) # force validation
         # TODO: make this work w/ u.to_datastruct() 
         return self.db.simple_edit(deployment_dep_args)

    def delete(self, token, deployment_dep_args):
        """
        Deletes a deployment.  The deployment_dep_args must only contain the id field.
        """
        u = DeploymentData.produce(deployment_dep_args,OP_DELETE) # force validation
        
        # check to see that what we are deleting exists
        rc = self.get(token, deployment_dep_args)
        if not rc:
            raise NoSuchObjectException()
        
        return self.db.simple_delete({ "id" : u.id })


    def list(self, token, deployment_dep_args):
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
         deployments.hostname,
         deployments.ip_address,
         deployments.mac_address,
         deployments.machine_id,
         deployments.image_id,
         deployments.state,
         deployments.display_name,
         deployments.puppet_node_diff,
         images.id,
         images.name,
         images.version,
         images.distribution_id,
         images.virt_storage_size,
         images.virt_ram,
         images.kickstart_metadata,
         images.kernel_options,
         images.valid_targets,
         images.is_container,
         images.puppet_classes,
         machines.id,
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
         machines.image_id
         FROM deployments,images,machines 
         WHERE images.id = deployments.image_id AND
         machines.id = deployments.machine_id
         LIMIT ?,?
         """ 

         results = self.db.cursor.execute(st, (offset,limit))
         results = self.db.cursor.fetchall()
         if results is None:
             return success([])

         deployments = []

         for x in results:

             image_data = image.ImageData.produce({
                    "id"                 : x[9],
                    "name"               : x[10],
                    "version"            : x[11],
                    "distribtuion_id"    : x[12],
                    "virt_storage_size"  : x[13],
                    "virt_ram"           : x[14],
                    "kickstart_metadata" : x[15],
                    "kernel_options"     : x[16],
                    "valid_targets"      : x[17],
                    "is_container"       : x[18],
                    "puppet_classes"     : x[19]
             }).to_datastruct(True)

             machine_data = machine.MachineData.produce({
                    "id"                 : x[20],
                    "hostname"           : x[21],
                    "ip_address"         : x[22],
                    "architecture"       : x[23],
                    "processor_speed"    : x[24],
                    "processor_count"    : x[25],
                    "memory"             : x[26],
                    "kernel_options"     : x[27],
                    "kickstart_metadata" : x[28],
                    "list_group"         : x[29],
                    "mac_address"        : x[30],
                    "is_container"       : x[31],
                    "image_id"           : x[32]
             }).to_datastruct(True)

             data = DeploymentData.produce({         
                "id"               : x[0],
                "hostname"         : x[1],
                "ip_address"       : x[2],
                "mac_address"      : x[3],
                "machine_id"       : x[4],
                "image_id"         : x[5],
                "state"            : x[6],
                "display_name"     : x[7],
                "puppet_node_diff" : x[8]
             }).to_datastruct(True)

             data["image"] = image_data
             data["machine"] = machine_data
             deployments.append(data)

         return success(deployments)


    def get_by_hostname(self, token, deployment_args):
        """
        Return a list of deployments for a given hostname. It is
        possible that there will be more than one result (since the
        hostname column is not unique).
        """

        if deployment_args.has_key("hostname"):
            hostname = deployment_args["hostname"]
        else:
            raise ValueError("hostname is required")

        result = self.db.simple_list({}, {"hostname": hostname})
        if (result.error_code != ERR_SUCCESS):
            return result
        self.insert_components(token, result.data)
        return success(result.data)
        
    def get(self, token, deployment_dep_args):
         """
         Return a specific deployment record.  Only the "id" is required in deployment_dep_args.
         """

         u = DeploymentData.produce(deployment_dep_args,OP_GET) # force validation

         st = """
         SELECT deployments.id,
         deployments.hostname, deployments.ip_address, deployments.mac_address,
         deployments.machine_id,deployments.image_id,deployments.state,
         deployments.display_name,
         deployments.puppet_node_diff,
         images.id, machines.id
         FROM deployments,images,machines WHERE deployments.id=:id AND 
         images.id = deployments.image_id AND machines.id = deployments.machine_id
         """

         self.db.cursor.execute(st,{ "id" : u.id })
         x = self.db.cursor.fetchone()
         if x is None:
             raise NoSuchObjectException()

         # exceptions will be raised by these next two calls, so no RC
         # checking is required
         machine_obj = machine.Machine()
         image_obj = image.Image()
         machine_results = machine_obj.get(token, { "id" : x[4] })
         image_results   = image_obj.get(token, { "id" : x[5] })

         data = DeploymentData.produce({
                "id"               : x[0],
                "hostname"         : x[1],
                "ip_address"       : x[2],
                "mac_address"      : x[3],
                "machine_id"       : x[4],
                "image_id"         : x[5],
                "state"            : x[6],
                "display_name"     : x[7],
                "puppet_node_diff" : x[8]
         }).to_datastruct(True)

         data["machine"] = machine_results.data
         data["image"]   = image_results.data

         return success(data)

    def insert_components(self, token, deployments):
        for deployment in deployments:
            if deployment["image_id"] is not None and deployment["image_id"] != -1:
                image_obj = image.Image()
                image_results = image_obj.get(token, {"id":deployment["image_id"]})
                if not image_results.ok():
                    raise OrphanedObjectException(comment="image_id")
                deployment["image"] = image_results.data
            if deployment["machine_id"] is not None and deployment["machine_id"] != -1:
                machine_obj = machine.Machine()
                machine_results = machine_obj.get(token, {"id":deployment["machine_id"]})
                if not machine_results.ok():
                    raise OrphanedObjectException(comment="machine_id")
                deployment["machine"] = machine_results.data


methods = Deployment()
register_rpc = methods.register_rpc
