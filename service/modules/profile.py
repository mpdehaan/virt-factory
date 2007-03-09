"""
Virt-factory backend code.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

from server.codes import *

import baseobj
import distribution
import cobbler
import provisioning
import web_svc

import os
import threading
import traceback

#------------------------------------------------------

class ProfileData(baseobj.BaseObject):

    FIELDS = [ "id", "name", "version", 
               "distribution_id", "virt_storage_size", "virt_ram",
               "kickstart_metadata", "kernel_options", "valid_targets",
               "is_container", "puppet_classes" ]

    def _produce(klass, profile_args,operation=None):
        """
        Factory method.  Create a profile object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the profile object.
        """

        self = ProfileData()
        self.from_datastruct(profile_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,profile_args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the profile as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        profile object for interaction with the ORM.  See methods below for examples.
        """
        return self.deserialize(profile_args)

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """
        return self.serialize()

    def validate(self,operation):
        """
        Cast variables appropriately and raise InvalidArgumentException
        where appropriate.
        """
        invalid_fields = {}
        
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            try:
                self.id = int(self.id)
            except:
                invalid_fields["id"] = REASON_FORMAT
 
        if operation in [OP_ADD, OP_EDIT]:
            # name is printable
            if not self.is_printable(self.name):
                invalid_fields["name"] = REASON_FORMAT

            # no restrictions on version other than printable?
            if not self.is_printable(self.version):
                invalid_fields["version"] = REASON_FORMAT

            # distribution_id references an existing distribution
            # this is actually done by the add and need not be done here
            # edit can't change it as it's not in the SQL code.

            # virt_storage_size is numeric or None
            if type(self.virt_storage_size) != int and self.virt_storage_size is not None:
                invalid_fields["virt_storage_size"] = REASON_FORMAT

            # virt_ram is numeric or None, and is >256
            if type(self.virt_ram) != int and self.virt_ram is not None:
                invalid_fields["virt_ram"] = REASON_FORMAT

            # kernel_options allows almost anything
            if self.kernel_options is not None and not self.is_printable(self.kernel_options):
                invalid_fields["kernel_options"] = REASON_FORMAT

            # valid_targets contains one of the valid_targets constants in codes.py
            if not self.valid_targets in VALID_TARGETS:
                invalid_fields["valid_targets"] = REASON_RANGE

            # is_container matches codes in codes.py
            if not self.is_container in VALID_CONTAINERS:
                invalid_fields["is_container"] = REASON_RANGE

            # puppet_classes should probably validate possible puppet classnames
            if self.puppet_classes is not None and not self.is_printable(self.puppet_classes):
                invalid_fields["puppet_classes"] = REASON_FORMAT

        if len(invalid_fields) > 0:
            print "invalid: ", invalid_fields
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


class Profile(web_svc.AuthWebSvc):

    add_edit = [ x for x in ProfileData.FIELDS]
    add_edit.remove("id") # probably need to tailor this further, but just using list fns for now

    DB_SCHEMA = {
        "table"  : "profiles",
        "fields" : ProfileData.FIELDS,
        "add"    : add_edit,
        "edit"   : add_edit
    }

    def __init__(self):
        self.methods = {"profile_add": self.add,
                        "profile_edit": self.edit,
                        "profile_delete": self.delete,
                        "profile_get": self.get,
                        "profile_list": self.list}
        web_svc.AuthWebSvc.__init__(self)
        self.db.db_schema = self.DB_SCHEMA

    def add(self, token, profile_args):
         """
         Create a profile.  profile_args should contain all fields except ID.
         """

         u = ProfileData.produce(profile_args,OP_ADD)

         if u.distribution_id is not None:
             try:
                 self.distribution = distribution.Distribution()
                 self.distribution.get(None, { "id" : u.distribution_id})
             except ShadowManagerException:
                 raise OrphanedObjectException(comment='distribution_id',traceback=traceback.format_exc())
         data = u.to_datastruct()
         self.cobbler_sync(data)
         return self.db.simple_add(data)
         
    def cobbler_sync(self, data):

         # make the corresponding cobbler calls.
         cobbler_api = cobbler.api.BootAPI()
         distributions = distribution.Distribution().list(None, {}).data
         provisioning.CobblerTranslatedProfile(cobbler_api ,distributions, data)

    def edit(self, token, profile_args):
         """
         Edit a profile.  profile_args should contain all fields that need to
         be changed.
         """

         u = ProfileData.produce(profile_args,OP_EDIT)
         data = u.to_datastruct()
         result = self.db.simple_edit(data)
         self.cobbler_sync(data)
         return result


    def delete(self, token, profile_args):
         """
         Deletes a profile.  The profile_args must only contain the id field.
         """

         u = ProfileData.produce(profile_args,OP_DELETE) # force validation

         machine_obj = machine.Machine()
         deployment_obj = profile.Proile()

         machines    = machine_obj.list(token, { "id" : u.machine_id })
         deployments = deployment_obj.list(token, { "id" : u.profile_id })
         
         # check to see that what we are deleting exists
         profile_result = self.get(None,u.to_datastruct())
         if not profile_result.error_code == 0:
            raise NoSuchObjectException(comment="profile_delete")

         if len(machines.data) > 0:
            raise OrphanedObjectException(comment="machine")
         if len(deployments.data) > 0:
            raise OrphanedObjectException(comment="deployment")
         
         return self.db.simple_delete({"id" : u.id })


    def list(self, token, profile_args):
         """
         Return a list of profiles.  The profile_args list is currently *NOT*
         used.  Ideally we need to include LIMIT information here for
         GUI pagination when we start worrying about hundreds of systems.
         """

         self.logger.debug("profile_list called")
         results =  self.db.nested_list (
                [ distribution.Distribution.DB_SCHEMA ],
                profile_args,
                { "distributions.id" : "profiles.distribution_id" }
         ) 
         self.logger.debug(results)
         return results


    def get(self, token, profile_args):
        """
        Return a specific profile record.  Only the "id" is required in profile_args.
        """

        u = ProfileData.produce(profile_args,OP_GET) # force validation
        result = self.db.nested_get([distribution.Distribution.DB_SCHEMA], u.to_datastruct(), {})
        
        if (result.error_code != ERR_SUCCESS):
            return result
        return success(result.data)

    def get_by_name(self, token, profile_args):
        """
        Return a specific profile profile record by name. Only the "name" is required
        in profile_args.
        """

        if profile_args.has_key("name"):
            name = profile_args["name"]
        else:
            raise ValueError("name is required")

        result = self.db.nested_list(
            [distribution.Distribution.DB_SCHEMA],
            {},
            {
                "profiles.name": "'%s'" % name,
                "profiles.distribution_id" : "distributions.id"
            }
        )
        if (result.error_code != ERR_SUCCESS):
            return result

        if (len(result.data) == 1):
            return success(result.data[0])
        else:
            return NoSuchObjectException(comment="get_by_name")


methods = Profile()
register_rpc = methods.register_rpc


