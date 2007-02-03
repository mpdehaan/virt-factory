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
import provisioning
import web_svc

import os
import threading
import traceback

#------------------------------------------------------

class ImageData(baseobj.BaseObject):

    FIELDS = [ "id", "name", "version", 
               "distribution_id", "virt_storage_size", "virt_ram",
               "kickstart_metadata", "kernel_options", "valid_targets",
               "is_container", "puppet_classes" ]

    def _produce(klass, image_args,operation=None):
        """
        Factory method.  Create a image object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the image object.
        """

        self = ImageData()
        self.from_datastruct(image_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,image_args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the image as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        image object for interaction with the ORM.  See methods below for examples.
        """

        self.id                 = self.load(image_args,"id")
        self.name               = self.load(image_args,"name")
        self.version            = self.load(image_args,"version")
        self.distribution_id    = self.load(image_args,"distribution_id")
        self.virt_storage_size  = self.load(image_args,"virt_storage_size")
        self.virt_ram           = self.load(image_args,"virt_ram")
        self.kickstart_metadata = self.load(image_args,"kickstart_metadata")
        self.kernel_options     = self.load(image_args,"kernel_options")
        self.valid_targets      = self.load(image_args,"valid_targets")
        self.is_container       = self.load(image_args,"is_container")
        self.puppet_classes     = self.load(image_args,"puppet_classes")

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


class Image(web_svc.AuthWebSvc):

    add_edit = [ x for x in ImageData.FIELDS]
    add_edit.remove("id") # probably need to tailor this further, but just using list fns for now

    DB_SCHEMA = {
        "table"  : "images",
        "fields" : ImageData.FIELDS,
        "add"    : add_edit,
        "edit"   : add_edit
    }

    def __init__(self):
        self.methods = {"image_add": self.add,
                        "image_edit": self.edit,
                        "image_delete": self.delete,
                        "image_get": self.get,
                        "image_list": self.list}
        web_svc.AuthWebSvc.__init__(self)
        self.db.db_schema = self.DB_SCHEMA

    def add(self, token, image_args):
         """
         Create a image.  image_args should contain all fields except ID.
         """

         st = """
         INSERT INTO images (name,version,
         distribution_id,virt_storage_size,virt_ram,kickstart_metadata,kernel_options,
         valid_targets,is_container, puppet_classes)
         VALUES (:name,:version,:distribution_id,
         :virt_storage_size,:virt_ram,:kickstart_metadata,:kernel_options,
         :valid_targets,:is_container, :puppet_classes)
         """
         u = ImageData.produce(image_args,OP_ADD)

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

         self.sync()
         
         return success(rowid)

    def sync(self):
        self.provisioning = provisioning.Provisioning()
        self.provisioning.sync(None, {} )


    def edit(self, token, image_args):
         """
         Edit a image.  image_args should contain all fields that need to
         be changed.
         """

         u = ImageData.produce(image_args,OP_EDIT) # force validation

         st = """
         UPDATE images 
         SET name=:name, version=:version, 
         virt_storage_size=:virt_storage_size, virt_ram=:virt_ram,
         kickstart_metadata=:kickstart_metadata,kernel_options=:kernel_options, 
         valid_targets=:valid_targets, is_container=:is_container,
         puppet_classes=:puppet_classes
         WHERE id=:id
         """

         self.db.cursor.execute(st, u.to_datastruct())
         self.db.connection.commit()

         self.sync()

         return success(u.to_datastruct(True))


    def delete(self, token, image_args):
         """
         Deletes a image.  The image_args must only contain the id field.
         """

         u = ImageData.produce(image_args,OP_DELETE) # force validation

         st = """
         DELETE FROM images WHERE images.id=:id
         """

         st2 = """
         SELECT images.id FROM deployments,images 
         WHERE deployments.image_id = images.id
         AND images.id=:id
         """

         st3 = """
         SELECT images.id FROM machines,images 
         WHERE machines.image_id = images.id
         AND images.id=:id
         """

         # check to see that what we are deleting exists
         image_result = self.get(None,u.to_datastruct())
         if not image_result.error_code == 0:
            raise NoSuchObjectException(comment="image_delete")

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

         # no need to sync provisioning as the image isn't hurting anything
         return success()


    def list(self, token, image_args):
         """
         Return a list of images.  The image_args list is currently *NOT*
         used.  Ideally we need to include LIMIT information here for
         GUI pagination when we start worrying about hundreds of systems.
         """

         offset = 0
         limit  = 100
         if image_args.has_key("offset"):
            offset = image_args["offset"]
         if image_args.has_key("limit"):
            limit = image_args["limit"]

         st = """
         SELECT 
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
         distributions.id,
         distributions.kernel,
         distributions.initrd,
         distributions.options,
         distributions.kickstart,
         distributions.name,
         distributions.architecture,
         distributions.kernel_options,
         distributions.kickstart_metadata
         FROM images 
         LEFT OUTER JOIN distributions ON images.distribution_id = distributions.id 
         LIMIT ?,?
         """ 

         results = self.db.cursor.execute(st, (offset,limit))
         results = self.db.cursor.fetchall()
         if results is None:
             return success([])

         images = []
         for x in results:
             # note that the distribution is *not* expanded as it may
             # not be valid in all cases
                 
             data = ImageData.produce({         
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

             images.append(data)

         return success(images)


    def get(self, token, image_args):
         """
         Return a specific image record.  Only the "id" is required in image_args.
         """

         u = ImageData.produce(image_args,OP_GET) # force validation

         st = """
         SELECT id,name,version,
         distribution_id,virt_storage_size,virt_ram,kickstart_metadata,kernel_options,
         valid_targets,is_container,puppet_classes
         FROM images WHERE id=:id
         """

         self.db.cursor.execute(st,{ "id" : u.id })
         x = self.db.cursor.fetchone()

         if x is None:
             raise NoSuchObjectException(comment="image_get")

         data = {
                "id"                 : x[0],
                "name"               : x[1],
                "version"            : x[2],
                "distribution_id"    : x[3],
                "virt_storage_size"  : x[4],
                "virt_ram"           : x[5],
                "kickstart_metadata" : x[6],
                "kernel_options"     : x[7],
                "valid_targets"      : x[8],
                "is_container"       : x[9],
                "puppet_classes"     : x[10]
         }

         data = ImageData.produce(data).to_datastruct(True)

         if x[3] is not None:
             distribution_obj = distribution.Distribution()
             distribution_results = distribution_obj.get(None, { "id" : x[3] })
             if not distribution_results.ok():
                 raise OrphanedObjectException(comment="distribution_id")
             data["distribution"] = distribution_results.data

         return success(data)



methods = Image()
register_rpc = methods.register_rpc

