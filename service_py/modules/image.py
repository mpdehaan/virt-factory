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
import distribution
import provisioning

#------------------------------------------------------

class Image(baseobj.BaseObject):

    def _produce(klass, image_args,operation=None):
        """
        Factory method.  Create a image object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the image object.
        """

        self = Image()
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
        self.filename           = self.load(image_args,"filename")
        self.specfile           = self.load(image_args,"specfile")
        self.distribution_id    = self.load(image_args,"distribution_id")
        self.virt_storage_size  = self.load(image_args,"virt_storage_size")
        self.virt_ram           = self.load(image_args,"virt_ram")
        self.kickstart_metadata = self.load(image_args,"kickstart_metadata")
        self.kernel_options     = self.load(image_args,"kernel_options")
        self.valid_targets      = self.load(image_args,"valid_targets")
        self.is_container       = self.load(image_args,"is_container")

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return {
            "id"                 : self.id,
            "name"               : self.name,
            "version"            : self.version,
            "filename"           : self.filename,
            "specfile"           : self.specfile,
            "distribution_id"    : self.distribution_id,
            "virt_storage_size"  : self.virt_storage_size,
            "virt_ram"           : self.virt_ram,
            "kickstart_metadata" : self.kickstart_metadata,
            "kernel_options"     : self.kernel_options,
            "valid_targets"      : self.valid_targets,
            "is_container"       : self.is_container  
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

            # filename references a file on the filesystem that is readable, or is None
            if not filename is None and notos.path.isfile(self.filename):
                invalid_fields["filename"] = REASON_NOFILE
            
            # specfile references a file on the filesystem that is readable, or is None
            if not specifle is None and not os.path.isfile(self.specfile):
                invalid_fields["specfile"] = REASON_NOFILE

            # either filename or specfile is not None
            if self.specfile is None and self.filename is None:
                invalid_fields["specfile"] = REASON_REQUIRED
                invalid_fields["filename"] = REASON_REQUIRED

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

        if len(invalid_fields) > 0:
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


#----------------------------------------------------------

def image_add(websvc,image_args):
     """
     Create a image.  image_args should contain all fields except ID.
     """

     st = """
     INSERT INTO images (name,version,filename,specfile,
     distribution_id,virt_storage_size,virt_ram,kickstart_metadata,kernel_options,
     valid_targets,is_container)
     VALUES (:name,:version,:filename,:specfile,:distribution_id,
     :virt_storage_size,:virt_ram,:kickstart_metadata,:kernel_options,
     :valid_targets,:is_container)
     """

     u = Image.produce(image_args,OP_ADD)

     if u.distribution_id is not None:
         try:
             distribution.distribution_get(websvc, { "id" : u.distribution_id})
         except ShadowManagerException:
             raise OrphanedObjectException(comment='distribution_id',traceback=traceback.format_exc())

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

     provisioning.provisioning_sync(websvc, {})

     return success(rowid)

#----------------------------------------------------------

def image_edit(websvc,image_args):
     """
     Edit a image.  image_args should contain all fields that need to
     be changed.
     """

     u = Image.produce(image_args,OP_EDIT) # force validation

     st = """
     UPDATE images 
     SET name=:name, version=:version, filename=:filename, specfile=:specfile,
     virt_storage_size=:virt_storage_size, virt_ram=:virt_ram,
     kickstart_metadata=:kickstart_metadata,kernel_options=:kernel_options, 
     valid_targets=:valid_targets, is_container=:is_container
     WHERE id=:id
     """

     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()

     provisioning.provisioning_sync(websvc,{})

     return success(u.to_datastruct(True))

#----------------------------------------------------------

def image_delete(websvc,image_args):
     """
     Deletes a image.  The image_args must only contain the id field.
     """

     u = Image.produce(image_args,OP_DELETE) # force validation
 
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
     image_result = image_get(websvc,u.to_datastruct())
     if not image_result.error_code == 0:
        raise NoSuchObjectException(comment="image_delete")

     # check to see that deletion won't orphan a deployment or machine
     websvc.cursor.execute(st2, { "id" : u.id })
     results = websvc.cursor.fetchall()
     if results is not None and len(results) != 0:
        raise OrphanedObjectException(comment="deployment")
     websvc.cursor.execute(st3, { "id" : u.id })
     results = websvc.cursor.fetchall()
     if results is not None and len(results) != 0:
        raise OrphanedObjectException(comment="machine")

     websvc.cursor.execute(st, { "id" : u.id })
     websvc.connection.commit()

     # no need to sync provisioning as the image isn't hurting anything
     return success()

#----------------------------------------------------------

def image_list(websvc,image_args):
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
     images.filename,
     images.specfile,
     images.distribution_id, 
     images.virt_storage_size,
     images.virt_ram,
     images.kickstart_metadata,
     images.kernel_options,
     images.valid_targets,
     images.is_container,
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

     results = websvc.cursor.execute(st, (offset,limit))
     results = websvc.cursor.fetchall()
     if results is None:
         return success([])

     images = []
     for x in results:
         # note that the distribution is *not* expanded as it may
         # not be valid in all cases
         data = Image.produce({         
            "id"        : x[0],
            "name"      : x[1],
            "version"   : x[2],
            "filename"  : x[3],
            "specfile"  : x[4],
            "distribution_id"    : x[5],
            "virt_storage_size"  : x[6],
            "virt_ram"           : x[7],
            "kickstart_metadata" : x[8],
            "kernel_options"     : x[9],
            "valid_targets"      : x[10],
            "is_container"       : x[11]
         }).to_datastruct(True)
     
         if x[12] is not None and x[12] != -1:
             data["distribution"] = distribution.Distribution.produce({
                 "id"                 : x[12],
                 "kernel"             : x[13],
                 "initrd"             : x[14],
                 "options"            : x[15],
                 "kickstart"          : x[16],
                 "name"               : x[17],
                 "architecture"       : x[18],
                 "kernel_options"     : x[19],
                 "kickstart_metadata" : x[20]
             }).to_datastruct(True)
     
         images.append(data)
  
     return success(images)

#--------------------------------------------------------

def image_get(websvc,image_args):
     """
     Return a specific image record.  Only the "id" is required in image_args.
     """

     u = Image.produce(image_args,OP_GET) # force validation

     st = """
     SELECT id,name,version,filename,specfile,
     distribution_id,virt_storage_size,virt_ram,kickstart_metadata,kernel_options,
     valid_targets,is_container
     FROM images WHERE id=:id
     """

     websvc.cursor.execute(st,{ "id" : u.id })
     x = websvc.cursor.fetchone()

     if x is None:
         raise NoSuchObjectException(comment="image_get")

     data = {
            "id"                 : x[0],
            "name"               : x[1],
            "version"            : x[2],
            "filename"           : x[3],
            "specfile"           : x[4],
            "distribution_id"    : x[5],
            "virt_storage_size"  : x[6],
            "virt_ram"           : x[7],
            "kickstart_metadata" : x[8],
            "kernel_options"     : x[9],
            "valid_targets"      : x[10],
            "is_container"       : x[11]
     }

     data = Image.produce(data).to_datastruct(True)

     if x[5] is not None:
         distribution_results = distribution.distribution_get(websvc, { "id" : x[5] })
         if not distribution_results.ok():
             raise OrphanedObjectException(comment="distribution_id")
         data["distribution"] = distribution_results.data

     return success(data)

#--------------------------------------------------------

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """

     handlers["image_add"]    = image_add
     handlers["image_delete"] = image_delete
     handlers["image_list"]   = image_list
     handlers["image_get"]    = image_get
     handlers["image_edit"]   = image_edit
