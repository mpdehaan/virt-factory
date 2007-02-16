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

        self.id                 = self.load(profile_args,"id")
        self.name               = self.load(profile_args,"name")
        self.version            = self.load(profile_args,"version")
        self.distribution_id    = self.load(profile_args,"distribution_id")
        self.virt_storage_size  = self.load(profile_args,"virt_storage_size")
        self.virt_ram           = self.load(profile_args,"virt_ram")
        self.kickstart_metadata = self.load(profile_args,"kickstart_metadata")
        self.kernel_options     = self.load(profile_args,"kernel_options")
        self.valid_targets      = self.load(profile_args,"valid_targets")
        self.is_container       = self.load(profile_args,"is_container")
        self.puppet_classes     = self.load(profile_args,"puppet_classes")

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return {
            "id"                 : self.id,
            "name"               : self.name,
            "version"            : self.version,
            "distribution_id"    : self.distribution_id,
            "virt_storage_size"  : self.virt_storage_size,
            "virt_ram"           : self.virt_ram,
            "kickstart_metadata" : self.kickstart_metadata,
            "kernel_options"     : self.kernel_options,
            "valid_targets"      : self.valid_targets,
            "is_container"       : self.is_container,
            "puppet_classes"     : self.puppet_classes  
        }

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

         st = """
         INSERT INTO profiles (name,version,
         distribution_id,virt_storage_size,virt_ram,kickstart_metadata,kernel_options,
         valid_targets,is_container, puppet_classes)
         VALUES (:name,:version,:distribution_id,
         :virt_storage_size,:virt_ram,:kickstart_metadata,:kernel_options,
         :valid_targets,:is_container, :puppet_classes)
         """
         u = ProfileData.produce(profile_args,OP_ADD)

         if u.distribution_id is not None:
             try:
                 self.distribution = distribution.Distribution()
                 self.distribution.get(None, { "id" : u.distribution_id})
             except ShadowManagerException:
                 raise OrphanedObjectException(comment='distribution_id',traceback=traceback.format_exc())

         lock = threading.Lock()
         lock.acquire()

         try:
             self.db.cursor.execute(st, u.to_datastruct())
             self.db.connection.commit()
         except Exception:
             lock.release()
             # FIXME: be more fined grained (find where IntegrityError is defined)
             raise SQLException(traceback=traceback.format_exc())

         rowid = self.db.cursor.lastrowid
         lock.release()

         self.cobbler_sync(u.to_datastruct()) 
     
         return success(rowid)
         
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

         u = ProfileData.produce(profile_args,OP_EDIT) # force validation

         st = """
         UPDATE profiles 
         SET name=:name, version=:version, 
         virt_storage_size=:virt_storage_size, virt_ram=:virt_ram,
         kickstart_metadata=:kickstart_metadata,kernel_options=:kernel_options, 
         valid_targets=:valid_targets, is_container=:is_container,
         puppet_classes=:puppet_classes
         WHERE id=:id
         """

         self.db.cursor.execute(st, u.to_datastruct())
         self.db.connection.commit()

         self.cobbler_sync(u.to_datastruct())

         return success(u.to_datastruct(True))


    def delete(self, token, profile_args):
         """
         Deletes a profile.  The profile_args must only contain the id field.
         """

         u = ProfileData.produce(profile_args,OP_DELETE) # force validation

         st = """
         DELETE FROM profiles WHERE profiles.id=:id
         """

         st2 = """
         SELECT profiles.id FROM deployments,profiles 
         WHERE deployments.profile_id = profiles.id
         AND profiles.id=:id
         """

         st3 = """
         SELECT profiles.id FROM machines,profiles 
         WHERE machines.profile_id = profiles.id
         AND profiles.id=:id
         """

         # check to see that what we are deleting exists
         profile_result = self.get(None,u.to_datastruct())
         if not profile_result.error_code == 0:
            raise NoSuchObjectException(comment="profile_delete")

         # check to see that deletion won't orphan a deployment or machine
         self.db.cursor.execute(st2, { "id" : u.id })
         results = self.db.cursor.fetchall()
         if results is not None and len(results) != 0:
            raise OrphanedObjectException(comment="deployment")
         self.db.cursor.execute(st3, { "id" : u.id })
         results = self.db.cursor.fetchall()
         if results is not None and len(results) != 0:
            raise OrphanedObjectException(comment="machine")

         self.db.cursor.execute(st, { "id" : u.id })
         self.db.connection.commit()

         return success()


    def list(self, token, profile_args):
         """
         Return a list of profiles.  The profile_args list is currently *NOT*
         used.  Ideally we need to include LIMIT information here for
         GUI pagination when we start worrying about hundreds of systems.
         """

         offset = 0
         limit  = 100
         if profile_args.has_key("offset"):
            offset = profile_args["offset"]
         if profile_args.has_key("limit"):
            limit = profile_args["limit"]

         st = """
         SELECT 
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
         distributions.id,
         distributions.kernel,
         distributions.initrd,
         distributions.options,
         distributions.kickstart,
         distributions.name,
         distributions.architecture,
         distributions.kernel_options,
         distributions.kickstart_metadata
         FROM profiles 
         LEFT OUTER JOIN distributions ON profiles.distribution_id = distributions.id 
         LIMIT ?,?
         """ 

         results = self.db.cursor.execute(st, (offset,limit))
         results = self.db.cursor.fetchall()
         if results is None:
             return success([])

         profiles = []
         for x in results:
             # note that the distribution is *not* expanded as it may
             # not be valid in all cases
                 
             data = ProfileData.produce({         
                "id"        : x[0],
                "name"      : x[1],
                "version"   : x[2],
                "distribution_id"    : x[3],
                "virt_storage_size"  : x[4],
                "virt_ram"           : x[5],
                "kickstart_metadata" : x[6],
                "kernel_options"     : x[7],
                "valid_targets"      : x[8],
                "is_container"       : x[9],
                "puppet_classes"     : x[10]
             }).to_datastruct(True)

             if x[11] is not None and x[11] != -1:
                 data["distribution"] = distribution.DistributionData.produce({
                     "id"                 : x[11],
                     "kernel"             : x[12],
                     "initrd"             : x[13],
                     "options"            : x[14],
                     "kickstart"          : x[15],
                     "name"               : x[16],
                     "architecture"       : x[17],
                     "kernel_options"     : x[18],
                     "kickstart_metadata" : x[19]
                 }).to_datastruct(True)

             profiles.append(data)

         return success(profiles)


    def get(self, token, profile_args):
        """
        Return a specific profile record.  Only the "id" is required in profile_args.
        """

        u = ProfileData.produce(profile_args,OP_GET) # force validation
        result = self.db.simple_get(u.to_datastruct())
        
        if (result.error_code != ERR_SUCCESS):
            return result
        self.insert_distribution(token, [result.data])
        return success(result.data)

    def insert_distribution(self, token, profiles):
        for profile in profiles:
            if profile["distribution_id"] is not None and profile["distribution_id"] != -1:
                distribution_obj = distribution.Distribution()
                distribution_results = distribution_obj.get(token, {"id":profile["distribution_id"]})
                if not distribution_results.ok():
                    raise OrphanedObjectException(comment="distribution_id")
                profile["distribution"] = distribution_results.data
                
    def get_by_name(self, token, profile_args):
        """
        Return a specific profile profile record by name. Only the "name" is required
        in profile_args.
        """

        if profile_args.has_key("name"):
            name = profile_args["name"]
        else:
            raise ValueError("name is required")

        result = self.db.simple_list({}, {"name": name})
        if (result.error_code != ERR_SUCCESS):
            return result
        self.insert_distribution(token, result.data)

        if (len(result.data) == 1):
            return success(result.data[0])
        else:
            return NoSuchObjectException(comment="get_by_name")


methods = Profile()
register_rpc = methods.register_rpc


