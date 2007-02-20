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

import profile
import machine
import web_svc

import traceback
import threading



#---------------------------------------------------------

class DeploymentData(baseobj.BaseObject):

    FIELDS = [ "id", "hostname", "ip_address", "registration_token", "mac_address", "machine_id", "profile_id",
               "state", "display_name", "puppet_node_diff", "netboot_enabled" ]

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
            if self.profile_id is None:
                passed = False
                invalid["profile_id"] = REASON_REQUIRED

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
    edit_fields.remove("profile_id")

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
         profilename = None

         try:
             machine_obj = machine.Machine()
             result = machine_obj.get(token, { "id" : deployment_dep_args["machine_id"]})
             mac = result.data["mac_address"]
         except ShadowManagerException:
             raise OrphanedObjectException(invalid_fields={'machine_id':REASON_ID})

         try:
             profile_obj = profile.Profile()
             result = profile_obj.get(token, { "id" : deployment_dep_args["profile_id"]})
             profilename = result.data["name"]
         except ShadowManagerException:
             raise OrphanedObjectException(invalid_fields={'profile_id':REASON_ID})

         display_name = mac + " / " + profilename

         deployment_dep_args["display_name"] = display_name
         deployment_dep_args["netboot_enabled"] = 0  # no PXE for virt yet, FIXME: add when supported by us.
         # NOTE: when adding PXE for virt, registration must disable it, to prevent reboot loop.
         # and we'll need some sort of virt/PXE WUI config monster :)
         
         u = DeploymentData.produce(deployment_dep_args,OP_ADD)
         self.cobbler_sync(u.to_datastruct())
         return self.db.simple_add(u.to_datastruct())

    def cobbler_sync(self, data):
         cobbler_api = cobbler.api.BootAPI()
         profiles = profile.Profile().list(None, {}).data
         provisioning.CobblerTranslatedSystem(cobbler_api, profiles, data)

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
             profile_obj = profile.Profile()
             result = profile_obj.get(token, { "id" : deployment_dep_args["profile_id"] })
             profilename = result.data["name"]
         except ShadowManagerException:
             raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

         display_name = mac + "/" + profilename
         deployment_dep_args["display_name"] = display_name

         u = DeploymentData.produce(deployment_dep_args,OP_EDIT) # force validation
         # TODO: make this work w/ u.to_datastruct() 
         self.cobbler_sync(u.to_datastruct())
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


    # required for compatibility with machine table for registration.
    def new(self, token):
        return self.add(token, {})


    def associate(self, token, machine_id, hostname, ip_addr, mac_addr, profile_id=None,
                  architecture=None, processor_speed=None, processor_count=None,
                  memory=None):
        """
        Associate a machine with an ip/host/mac address
        """
        print "associating..."
        # determine the profile from the token. 
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

        if results.data[0].has_key("profile_id"):
            profile_id = results.data[0]["profile_id"]

        # NOTE: it looks like the deployments table has no way to specify
        # the number of virtual CPU's requested.  This is true.  It comes
        # from the profile.  There is nothing to be gained from what
        # registration would tell us because we set it originally, thus
        # we already know.  Someone /could/ have tweaked it on the guest,
        # but it doesn't really affect how we manage it.
        args = {
            'id': machine_id,
            'hostname': hostname,
            'ip_address': ip_addr,
            'mac_address': mac_addr,
            'profile_id': profile_id,
            'state' : 'registered',
            'netboot_enabled' : 0    # important, prevent possible PXE install loop.
        }
        print args

        return self.edit(token, args)

    

    ## BIG FIXME:  NEEDS AN ASSOCIATE METHOD, JUST LIKE MACHINE, FOR VIRTY REGISTRATION
    ## (that, and virty registration needs to indicate virtness so the right method is called!)

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
         deployments.registration_token,
         deployments.mac_address,
         deployments.machine_id,
         deployments.profile_id,
         deployments.state,
         deployments.display_name,
         deployments.puppet_node_diff,
         deployments.netboot_enabled,
         profiles.id,
         profiles.name,
         profiles.version,
         profiles.distribution_id,
         profiles.virt_storage_size,
         profiles.virt_ram,
         profiles.kickstart_metadata,
         profiles.kernel_options,
         profiles.valid_targets,
         profiles.is_container,
         profiles.puppet_classes,
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
         machines.profile_id
         FROM deployments,profiles,machines 
         WHERE profiles.id = deployments.profile_id AND
         machines.id = deployments.machine_id
         LIMIT ?,?
         """ 

         results = self.db.cursor.execute(st, (offset,limit))
         results = self.db.cursor.fetchall()
         if results is None:
             return success([])

         deployments = []

         for x in results:

             profile_data = profile.ProfileData.produce({
                    "id"                 : x[10],
                    "name"               : x[11],
                    "version"            : x[12],
                    "distribtuion_id"    : x[13],
                    "virt_storage_size"  : x[14],
                    "virt_ram"           : x[15],
                    "kickstart_metadata" : x[16],
                    "kernel_options"     : x[17],
                    "valid_targets"      : x[18],
                    "is_container"       : x[19],
                    "puppet_classes"     : x[20]
             }).to_datastruct(True)

             machine_data = machine.MachineData.produce({
                    "id"                 : x[21],
                    "hostname"           : x[22],
                    "ip_address"         : x[23],
                    "architecture"       : x[24],
                    "processor_speed"    : x[25],
                    "processor_count"    : x[26],
                    "memory"             : x[27],
                    "kernel_options"     : x[28],
                    "kickstart_metadata" : x[29],
                    "list_group"         : x[30],
                    "mac_address"        : x[31],
                    "is_container"       : x[32],
                    "profile_id"         : x[33]
             }).to_datastruct(True)

             data = DeploymentData.produce({         
                "id"                 : x[0],
                "hostname"           : x[1],
                "ip_address"         : x[2],
                "registration_token" : x[3]
                "mac_address"        : x[4],
                "machine_id"         : x[5],
                "profile_id"         : x[6],
                "state"              : x[7],
                "display_name"       : x[8],
                "puppet_node_diff"   : x[9],
                "netboot_enabled"    : x[10]
             }).to_datastruct(True)

             data["profile"] = profile_data
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
         deployments.hostname, deployments.ip_address, deployments.registration_token, deployments.mac_address,
         deployments.machine_id, deployments.profile_id, deployments.state,
         deployments.display_name,
         deployments.puppet_node_diff, deployments.netboot_enabled,
         profiles.id, machines.id
         FROM deployments,profiles,machines WHERE deployments.id=:id AND 
         profiles.id = deployments.profile_id AND machines.id = deployments.machine_id
         """

         self.db.cursor.execute(st,{ "id" : u.id })
         x = self.db.cursor.fetchone()
         if x is None:
             raise NoSuchObjectException()

         # exceptions will be raised by these next two calls, so no RC
         # checking is required
         machine_obj = machine.Machine()
         profile_obj = profile.Profile()
         machine_results = machine_obj.get(token, { "id" : x[5] })
         profile_results   = profile_obj.get(token, { "id" : x[6] })

         data = DeploymentData.produce({
                "id"                 : x[0],
                "hostname"           : x[1],
                "ip_address"         : x[2],
                "registration_token" : x[3],
                "mac_address"        : x[4],
                "machine_id"         : x[5],
                "profile_id"         : x[6],
                "state"              : x[7],
                "display_name"       : x[8],
                "puppet_node_diff"   : x[9],
         }).to_datastruct(True)

         data["machine"] = machine_results.data
         data["profile"]   = profile_results.data

         return success(data)

    def insert_components(self, token, deployments):
        for deployment in deployments:
            if deployment["profile_id"] is not None and deployment["profile_id"] != -1:
                profile_obj = profile.Profile()
                profile_results = profile_obj.get(token, {"id":deployment["profile_id"]})
                if not profile_results.ok():
                    raise OrphanedObjectException(comment="profile_id")
                deployment["profile"] = profile_results.data
            if deployment["machine_id"] is not None and deployment["machine_id"] != -1:
                machine_obj = machine.Machine()
                machine_results = machine_obj.get(token, {"id":deployment["machine_id"]})
                if not machine_results.ok():
                    raise OrphanedObjectException(comment="machine_id")
                deployment["machine"] = machine_results.data


methods = Deployment()
register_rpc = methods.register_rpc

