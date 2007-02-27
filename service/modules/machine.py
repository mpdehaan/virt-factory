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

import profile
import cobbler
import provisioning
import web_svc
import regtoken
import deployment

import threading
import traceback

#------------------------------------------------------

class MachineData(baseobj.BaseObject):

    FIELDS = [ "id", "hostname", "ip_address", "registration_token", "architecture", "processor_speed", "processor_count", "memory",
               "kernel_options", "kickstart_metadata", "list_group", "mac_address", "is_container",
               "profile_id", "puppet_node_diff", "netboot_enabled", "is_locked" ]

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

        return self.deserialize(machine_args)

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return self.serialize()

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
        u = MachineData.produce(args,OP_ADD)
        if u.profile_id is not None:
            print "creating an profile.Profile()" 
            try:
                self.profile = profile.Profile()
                self.profile.get( token, { "id" : u.profile_id } )
            except ShadowManagerException:
                raise OrphanedObjectException(comment="profile_id")

        # TODO: generate the registration token here and make it actually random and decent.
        u.registration_token = regtoken.RegToken().generate(token)
        u.netboot_enabled = 1 # initially, allow PXE, until it registers
        result = self.db.simple_add(u.to_datastruct())
        if u.profile_id >= 0:
            self.cobbler_sync(machine_args)
        return result

    def cobbler_sync(self, data):
        cobbler_api = cobbler.api.BootAPI()
        profiles = profile.Profile().list(None, {}).data
        provisioning.CobblerTranslatedSystem(cobbler_api, profiles, data)
 
    def new(self, token):
        """
        Allocate a new machine record to be fill in later. Return a machine_id
        """

        args = { "profile_id" : -1 }
        return self.add(token, args)


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

        if len(results.data) > 0 and results.data[0].has_key("profile_id"):
            profile_id = results.data[0]["profile_id"]

        if profile_id is None:
            profile_id = -1  # the unassigned profile id

        args = {
            'id': machine_id,
            'hostname': hostname,
            'ip_address': ip_addr,
            'mac_address': mac_addr,
            'profile_id': profile_id,
            'architecture' : architecture,
            'processor_speed' : processor_speed,
            'processor_count' : processor_count,
            'netboot_enabled' : 0, # elimiinate PXE install loop
            'memory' : memory
        }
        print args
        return self.edit(token, args)
        
    def edit(self, token, machine_args):
        """
        Edit a machine.
        """
        
        u = MachineData.produce(machine_args,OP_EDIT) # force validation
        if u.profile_id is not None:
            try:
                profile_obj = profile.Profile()
                profile_obj.get(token, { "id" : u.profile_id })
            except ShadowManagerException:
                raise OrphanedObjectException(comments="no profile found",invalid_fields={"profile_id":REASON_ID})

        # TODO: make this work w/ u.to_datastruct() 
        result = self.db.simple_edit(machine_args)
        if u.profile_id >= 0:
            sync_args = self.get(token, { "id" : machine_args["id"] })
            self.cobbler_sync(sync_args.data)
        return result

    def delete(self, token, args):
        """
        Deletes a machine.  The machine_args must only contain the id field.
        """
        
        u = MachineData.produce(args,OP_DELETE) # force validation
        
        deployment_obj = deployment.Deployment()
        deployments = deployment_obj.db.simple_list({}, {"machine_id" : u.id })
        if len(deployments.data) > 0:
            raise OrphanedObjectException(comment="deployment")
        
        return self.db.simple_delete(args)

    def list(self, token, machine_args):
        """
        Return a list of machines.  The machine_args list is currently *NOT*
        used.  Ideally we need to include LIMIT information here for
        GUI pagination when we start worrying about hundreds of systems.
        """

        return self.db.nested_list (
            [ profile.Profile.DB_SCHEMA ],
            machine_args,
            {
                "machines.profile_id" : "profiles.id"
            } 
        )

    def get_by_hostname(self, token, machine_args):
        """
        Return a list of machines for a given hostname. It is
        possible that there will be more than one result (since the
        hostname column is not unique).
        """

        if machine_args.has_key("hostname"):
            hostname = machine_args["hostname"]
        else:
            # FIXME: this should be a shadowmanager exception if API is exposed remotely
            raise ValueError("hostname is required")

        result = self.db.nested_list(
            [profile.Profile.DB_SCHEMA],
            machine_args,
            {
                "hostname": "'%s'" % hostname,
                "machines.profile_id" : "profiles.id"
            }
        )
        if (result.error_code != ERR_SUCCESS):
            return result
        return success(result.data)
        
    def get_by_regtoken(self, token, args):
        """
        Internal use only.  Find if any machines have a given regtoken.
        """
        return self.db.nested_list(
            [profile.Profile.DB_SCHEMA],
            {},
            {
                "registration_token" : "'%s'" % args["registration_token"],
                "machines.profile_id" : "profiles.id"
            }
        )

    def get(self, token, machine_args):
        """
        Return a specific machine record.  Only the "id" is required in machine_args.
        """
        
        u = MachineData.produce(machine_args,OP_GET) # force validation
        return self.db.simple_get(u.to_datastruct())

methods = Machine()
register_rpc = methods.register_rpc


