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
from errors import *
import baseobj
import traceback
import threading
import distribution
import provisioning

class Image(baseobj.BaseObject):

    def _produce(klass, args,operation=None):
        """
        Factory method.  Create a image object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the image object.
        """

        self = Image()
        self.from_datastruct(args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the image as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        image object for interaction with the ORM.  See methods below for examples.
        """

        self.id                 = self.load(args,"id")
        self.name               = self.load(args,"name")
        self.version            = self.load(args,"version")
        self.filename           = self.load(args,"filename")
        self.specfile           = self.load(args,"specfile")
        self.distribution_id    = self.load(args,"distribution_id")
        self.virt_storage_size  = self.load(args,"virt_storage_size")
        self.virt_ram           = self.load(args,"virt_ram")
        self.kickstart_metadata = self.load(args,"kickstart_metadata")
        self.kernel_options     = self.load(args,"kernel_options")

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
            "kernel_options"     : self.kernel_options  
        }

    def validate(self,operation):
        """
        Cast variables appropriately and raise InvalidArgumentException
        where appropriate.
        """
        # FIXME
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def image_add(websvc,args):
     """
     Create a image.  args should contain all fields except ID.
     """

     st = """
     INSERT INTO images (name,version,filename,specfile,
     distribution_id,virt_storage_size,virt_ram,kickstart_metadata,kernel_options)
     VALUES (:name,:version,:filename,:specfile,:distribution_id,
     :virt_storage_size,:virt_ram,:kickstart_metadata,:kernel_options)
     """

     u = Image.produce(args,OP_ADD)

     if u.distribution_id is not None:
         try:
             distribution.distribution_get(websvc, { "id" : u.distribution_id})
         except ShadowManagerException:
             raise OrphanedObjectExcception('distribution_id')

     lock = threading.Lock()
     lock.acquire()

     try:
         websvc.cursor.execute(st, u.to_datastruct())
         websvc.connection.commit()
     except Exception:
         lock.release()
         # FIXME: be more fined grained (find where IntegrityError is defined)
         raise SQLException(traceback.format_exc())

     id = websvc.cursor.lastrowid
     lock.release()

     provisioning.provisioning_sync(websvc, {})

     return success(id)

def image_edit(websvc,args):
     """
     Edit a image.  args should contain all fields that need to
     be changed.
     """

     u = Image.produce(args,OP_EDIT) # force validation

     st = """
     UPDATE images 
     SET name=:name, version=:version, filename=:filename, specfile=:specfile,
     virt_storage_size=:virt_storage_size, virt_ram=:virt_ram,
     kickstart_metadata=:kickstart_metadata,kernel_options=:kernel_options
     WHERE id=:id
     """

     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()

     provisioning.provisioning_sync(websvc,{})

     return success(u.to_datastruct(True))

def image_delete(websvc,args):
     """
     Deletes a image.  The args must only contain the id field.
     """

     u = Image.produce(args,OP_DELETE) # force validation
 
     st = """
     DELETE FROM images WHERE images.id=:id
     """

     st2 = """
     SELECT images.id FROM deployments,images 
     WHERE deployments.image_id = images.id
     AND images.id=:id
     """

     # check to see that what we are deleting exists
     (rc, data) = image_get(websvc,u.to_datastruct())
     if not rc == 0:
        raise NoSuchObjectException("image_delete")

     # check to see that deletion won't orphan a deployment
     websvc.cursor.execute(st2, { "id" : u.id })
     results = websvc.cursor.fetchall()
     if results is not None and len(results) != 0:
        raise OrphanedObjectException("deployment")

     websvc.cursor.execute(st, { "id" : u.id })
     websvc.connection.commit()

     # no need to sync provisioning as the image isn't hurting anything
     return success()

def image_list(websvc,args):
     """
     Return a list of images.  The args list is currently *NOT*
     used.  Ideally we need to include LIMIT information here for
     GUI pagination when we start worrying about hundreds of systems.
     """

     offset = 0
     limit  = 100
     if args.has_key("offset"):
        offset = args["offset"]
     if args.has_key("limit"):
        limit = args["limit"]

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
            "distribution_id"    : x[9],
            "virt_storage_size"  : x[6],
            "virt_ram"           : x[7],
            "kickstart_metadata" : x[8],
            "kernel_options"     : x[9]
         }).to_datastruct(True)
     
         if x[10] is not None and x[10] != -1:
             data["distribution"] = distribution.Distribution.produce({
                 "id"             : x[10],
                 "kernel"         : x[11],
                 "initrd"         : x[12],
                 "options"        : x[13],
                 "kickstart"      : x[14],
                 "name"           : x[15],
                 "architecture"   : x[16],
                 "kernel_options" : x[17],
                 "kickstart_metadata" : x[18]
             }).to_datastruct(True)
     
         images.append(data)
  
     return success(images)

def image_get(websvc,args):
     """
     Return a specific image record.  Only the "id" is required in args.
     """

     u = Image.produce(args,OP_GET) # force validation

     st = """
     SELECT id,name,version,filename,specfile,
     distribution_id,virt_storage_size,virt_ram,kickstart_metadata,kernel_options
     FROM images WHERE id=:id
     """

     websvc.cursor.execute(st,{ "id" : u.id })
     x = websvc.cursor.fetchone()

     if x is None:
         raise NoSuchObjectException("image_get")

     data = {
            "id"       : x[0],
            "name"     : x[1],
            "version"  : x[2],
            "filename" : x[3],
            "specfile" : x[4],
            "distribution_id" : x[5],
            "virt_storage_size" : x[6],
            "virt_ram" : x[7],
            "kickstart_metadata" : x[8],
            "kernel_options" : x[9]
     }

     data = Image.produce(data).to_datastruct(True)

     if x[5] is not None:
         (rc, dist) = distribution.distribution_get(websvc, { "id" : x[5] })
         if rc != 0:
             raise OrphanedObjectException("distribution_id")
         data["distribution"] = dist

     return success(data)

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """

     handlers["image_add"]    = image_add
     handlers["image_delete"] = image_delete
     handlers["image_list"]   = image_list
     handlers["image_get"]    = image_get
     handlers["image_edit"]   = image_edit

