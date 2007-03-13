#!/usr/bin/python

## Virt-factory backend code.
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


from server.codes import *

import baseobj
import profile
import machine
import web_svc
import task
import regtoken
import provisioning
import nodecomm

import socket
import traceback
import threading
import cobbler.api



#---------------------------------------------------------

class DeploymentData(baseobj.BaseObject):

    FIELDS = [ "id", "hostname", "ip_address", "registration_token", "mac_address", "machine_id", "profile_id",
               "state", "display_name", "netboot_enabled", "puppet_node_diff", "is_locked" ]

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
        Load object from hash
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
            raise InvalidArgumentsException("bad token")
        # FIXME: check that at least some results are returned.

        if results.data[0].has_key("profile_id"):
            profile_id = results.data[0]["profile_id"]

        return self.edit({
            'id': machine_id,
            'hostname': hostname,
            'ip_address': ip_addr,
            'mac_address': mac_addr,
            'profile_id': profile_id
         })

    def cobbler_sync(self, data):
         cobbler_api = cobbler.api.BootAPI()
         profiles = profile.Profile().list(None, {}).data
         provisioning.CobblerTranslatedSystem(cobbler_api, profiles, data, is_virtual=True)

    # for duck typing compatibility w/ machine           
    def new(self, token):
         args = {}
         print "deployment_new"
         return self.add(token, args)    

    def add(self, token, deployment_dep_args):
         """
         Create a deployment.  deployment_dep_args should contain all fields except ID.
         """
         mac = None
         profilename = None

         # find highest deployment id
         all_deployments = self.list(token, {})

         try:
             machine_obj = machine.Machine()
             machine_result = machine_obj.get(token, { "id" : deployment_dep_args["machine_id"]})
             mac = machine_result.data["mac_address"]
         except VirtFactoryException:
             raise OrphanedObjectException(invalid_fields={'machine_id':REASON_ID})

         try:
             profile_obj = profile.Profile()
             result = profile_obj.get(token, { "id" : deployment_dep_args["profile_id"]})
             profilename = result.data["name"]
         except VirtFactoryException:
             raise OrphanedObjectException(invalid_fields={'profile_id':REASON_ID})

         display_name = mac + " / " + profilename

         deployment_dep_args["display_name"] = display_name
         deployment_dep_args["netboot_enabled"] = 0
         deployment_dep_args["mac_address"] = self.generate_mac_address(all_deployments.data[-1]["id"])
         deployment_dep_args["state"] = DEPLOYMENT_STATE_CREATING
         deployment_dep_args["netboot_enabled"] = 0 # never PXE's
         deployment_dep_args["registration_token"] = regtoken.RegToken().generate(token)

         # cobbler sync must run with a filled in item in the database, so we must commit
         # prior to running cobbler sync
         u = DeploymentData.produce(deployment_dep_args,OP_ADD)
         results = self.db.simple_add(u.to_datastruct())
         sync_args = self.get(token, { "id" : results.data }).data
         self.cobbler_sync(sync_args)

         
         handle = nodecomm.get_handle(socket.gethostname(), machine_result.data["hostname"])
         
         deployment_dep_args["id"] = results.data
         self.__queue_operation(token, deployment_dep_args, TASK_OPERATION_INSTALL_VIRT) 
         return success() 

    def generate_mac_address(self, id):
         # pick an offset into the XenSource range as given by the highest used object id
         # FIXME: verify that sqlite id fields work as counters and don't fill in on deletes
         # FIXME: verify math below
         x = id + 1
         high = x / (127*256)
         mid  = (x % (127*256)) / 256
         low  = x % 256 
         return ":".join([ "00", "16", "3E", "%02x" % high, "%02x" % mid, "%02x" % low ])

    def edit(self, token, deployment_dep_args):
         """
         Edit a deployment.  deployment_dep_args should contain all fields that need to
         be changed.
         """

         try:
             machine_obj = machine.Machine()
             result = machine_obj.get(token, { "id" : deployment_dep_args["machine_id"]})
             mac = result.data["mac_address"]
         except VirtFactoryException:
             raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

         try:
             profile_obj = profile.Profile()
             result = profile_obj.get(token, { "id" : deployment_dep_args["profile_id"] })
             profilename = result.data["name"]
         except VirtFactoryException:
             raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

         display_name = mac + "/" + profilename
         deployment_dep_args["display_name"] = display_name
         

         u = DeploymentData.produce(deployment_dep_args,OP_EDIT) # force validation
         deployment_dep_args["netboot_enabled"] = 0 # never PXE's

         results = self.db.simple_edit(deployment_dep_args)
         sync_args = self.get(token, { "id" : u.id })
         self.cobbler_sync(sync_args.data)
         return results

    def __set_locked(self, token, args, dep_state=DEPLOYMENT_STATE_PENDING, lock=True):
        obj = self.get(token, { "id" : args["id"] })
        if not obj.ok():
            raise NoSuchObjectException()
        args = obj.data
        args["state"] = dep_state
        if lock:
            args["is_locked"] = 1
        else:
            args["is_locked"] = 0
        self.edit(token, args)
     
    def set_state(self, token, args, status_code):
        obj = self.get(token, { "id" : args["id"] })
        if not obj.ok():
            raise NoSuchObjectException()
        args = obj.data
        args["state"] = status_code
        self.edit(token, args)

    def delete(self, token, args):
        self.__set_locked(token, args, DEPLOYMENT_STATE_DELETING, True)
        self.__queue_operation(token, args, TASK_OPERATION_DELETE_VIRT)
        return success() # FIXME: always?

    def pause(self, token, args):
        self.__set_locked(token, args, DEPLOYMENT_STATE_PAUSING, True)
        self.__queue_operation(token, args, TASK_OPERATION_PAUSE_VIRT)
        return success()

    def unpause(self, token, args):
        self.__set_locked(token, args, DEPLOYMENT_STATE_UNPAUSING, True)
        self.__queue_operation(token, args, TASK_OPERATION_UNPAUSE_VIRT)
        return success()

    def shutdown(self, token, args):
        self.__set_locked(token, args, DEPLOYMENT_STATE_STOPPING, True)
        self.__queue_operation(token, args, TASK_OPERATION_SHUTDOWN_VIRT)
        return success()

    def start(self, token, args):
        self.__set_locked(token, args, DEPLOYMENT_STATE_STARTING, True)
        self.__queue_operation(token, args, TASK_OPERATION_START_VIRT)
        return success()

    def database_delete(self, token, deployment_dep_args):
        """
        Deletes a deployment.  The deployment_dep_args must only contain the id field.
        """
        u = DeploymentData.produce(deployment_dep_args,OP_DELETE) # force validation
        
        # check to see that what we are deleting exists
        rc = self.get(token, deployment_dep_args)
        if not rc:
            raise NoSuchObjectException()
        
        return self.db.simple_delete({ "id" : u.id })


    def list(self, token, args):
        """
        Return a list of deployments.  The deployment_dep_args list is currently *NOT*
        used.  Ideally we need to include LIMIT information here for
        GUI pagination when we start worrying about hundreds of systems.
        """

        return self.db.nested_list(
            [
                machine.Machine.DB_SCHEMA, 
                profile.Profile.DB_SCHEMA
            ],
            args,
            {
                "machines.id"    : "deployments.machine_id",
                "profiles.id"    : "deployments.profile_id" 
            },
        )

    def __queue_operation(self, token, args, task_operation):
        
         obj = self.get(token, { "id" : args["id"] })
         if not obj.ok():
             raise NoSuchObjectException()

         task_obj = task.Task()
         task_obj.add(token, {
            "user_id"       : -1,  # FIXME: obtain from token
            "machine_id"    : args["machine_id"],
            "deployment_id" : args["id"],
            "action_type"   : task_operation,
            "state"         : TASK_STATE_QUEUED
         })


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

        return self.db.nested_list(
            [
                machine.Machine.DB_SCHEMA, 
                profile.Profile.DB_SCHEMA
            ],
            {},
            {
                "deployments.hostname" : "'%s'" % hostname,
                "machines.id"          : "deployments.machine_id",
                "profiles.id"          : "deployments.profile_id" 
            },
        )


    def _get_by_regtoken(self, token, args):
        """
        Internal use only.  Find if any deployments have a given regtoken.
        """
        return self.db.nested_list(
            [
                machine.Machine.DB_SCHEMA, 
                profile.Profile.DB_SCHEMA
            ],
            {},
            {
                "registration_token" : '"%s"' % args["registration_token"],
                "machines.id"    : "deployments.machine_id",
                "profiles.id"    : "deployments.profile_id" 
            },
        )

        
    def get(self, token, args):
         """
         Return a specific deployment record.  Only the "id" is required in deployment_dep_args.
         """

         return self.db.nested_get([profile.Profile.DB_SCHEMA, machine.Machine.DB_SCHEMA], args)



methods = Deployment()
register_rpc = methods.register_rpc

