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


import base64
from codes import *
from errors import *
import baseobj
import traceback
import threading
import provisioning

class Distribution(baseobj.BaseObject):

    def _produce(klass, args,operation=None):
        """
        Factory method.  Create a distribution object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the distribution object.
        """

        self = Distribution()
        self.from_datastruct(args)
        self.validate(operation)

        return self

    produce = classmethod(_produce)

    def from_datastruct(self,args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the distribution as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        distribution object for interaction with the ORM.  See methods below for examples.
        """

        self.id           = self.load(args,"id")
        self.kernel       = self.load(args,"kernel")
        self.initrd       = self.load(args,"initrd")
        self.options      = self.load(args,"options")
        self.kickstart    = self.load(args,"kickstart")
        self.name         = self.load(args,"name")
        self.architecture = self.load(args,"architecture") 
        self.kernel_options = self.load(args,"kernel_options")
        self.kickstart_metadata = self.load(args,"kickstart_metadata")

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return {
            "id"           : self.id,
            "kernel"       : self.kernel,
            "initrd"       : self.initrd,
            "options"      : self.options,
            "kickstart"    : self.kickstart,
            "name"         : self.name,
            "architecture" : self.architecture,
            "kernel_options" : self.kernel_options,
            "kickstart_metadata" : self.kickstart_metadata
        }

    def validate(self,operation):

        if self.id is None:
            # -1 is for sqlite to say "use your own counter".
            self.id = -1 

        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def distribution_add(websvc,args):
     """
     Create a distribution.  args should contain all distribution fields except ID.
     """

     u = Distribution.produce(args,OP_ADD)

     st = """
     INSERT INTO distributions (kernel,initrd,options,kickstart,name,architecture,kickstart_metadata)
     VALUES (:kernel,:initrd,:options,:kickstart,:name, :architecture, :kickstart_metadata)
     """

     lock = threading.Lock()
     lock.acquire()

     try:
         websvc.cursor.execute(st, u.to_datastruct())
         websvc.connection.commit()
     except Exception:
         lock.release()
         raise SQLException(traceback.format_exc())

     id = websvc.cursor.lastrowid
     lock.release()
     provisioning.provisioning_sync(websvc,{})

     return success(id)

def distribution_edit(websvc,args): 

     u = Distribution.produce(args,OP_EDIT)

     st = """
     UPDATE distributions SET
     kernel=:kernel,
     initrd=:initrd,
     options=:options,
     kickstart=:kickstart,
     name=:name,
     architecture=:architecture,
     kernel_options=:kernel_options,
     kickstart_metadata=:kickstart_metadata
     WHERE id=:id
     """

     ds = u.to_datastruct()
     websvc.cursor.execute(st, ds)
     websvc.connection.commit()
     provisioning.provisioning_sync(websvc,{})

     return success(u.to_datastruct())

def distribution_delete(websvc,args):

     st = """
     SELECT machines.id FROM machines, distributions WHERE
     machines.distribution_id = distributions.id AND
     distributions.id = :id
     """

     u = Distribution.produce(args)
     websvc.cursor.execute(st,u.to_datastruct())
     x = websvc.cursor.fetchone()
     if x is not None:
         raise OrphanedObjectException("machines.distribution_id")

     st = """
     SELECT images.id FROM images, distributions WHERE
     images.distribution_id = distributions.id
     """

     websvc.cursor.execute(st, u.to_datastruct())
     x = websvc.cursor.fetchone()
     if x is not None:
         raise OrphanedObjectException("images.distribution_id")
     u = Distribution.produce(args,OP_DELETE) # force validation

     st = """
     DELETE FROM distributions WHERE distributions.id=:id
     """

     websvc.cursor.execute(st, { "id" : u.id })
     websvc.connection.commit()

     return success()

def distribution_list(websvc,args):
     """
     Return a list of distributions.  The args list is currently *NOT*
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
     SELECT id,kernel,initrd,options,kickstart,name,architecture,kernel_options,kickstart_metadata
     FROM distributions LIMIT ?,?
     """ 

     results = websvc.cursor.execute(st, (offset,limit))
     results = websvc.cursor.fetchall()
     distributions = []

     for x in results:
         data = {         
            "id"           : x[0],
            "kernel"       : x[1],
            "initrd"       : x[2],
            "options"      : x[3],
            "kickstart"    : x[4],
            "name"         : x[5],
            "architecture" : x[6],
            "kernel_options" : x[7],
            "kickstart_metadata" : x[8]
         }
         distributions.append(Distribution.produce(data).to_datastruct())
     return success(distributions)

def distribution_get(websvc,args):
     """
     Return a specific distribution record.  Only the "id" is required in args.
     """

     u = Distribution.produce(args,OP_GET) # force validation

     st = """
     SELECT id,kernel,initrd,options,kickstart,name,architecture,kernel_options,kickstart_metadata
     FROM distributions WHERE distributions.id=:id
     """

     websvc.cursor.execute(st,{ "id" : u.id })
     x = websvc.cursor.fetchone()
     if x is None:
         raise NoSuchObjectException("distribution_get")

     data = {
            "id"               : x[0],
            "kernel"           : x[1],
            "initrd"           : x[2],
            "options"          : x[3],
            "kickstart"        : x[4],
            "name"             : x[5],
            "architecture"     : x[6],
            "kernel_options"   : x[7],
            "kickstart_metadata" : x[8]
     }

     return success(Distribution.produce(data).to_datastruct())

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """

     handlers["distribution_add"]    = distribution_add
     handlers["distribution_delete"] = distribution_delete
     handlers["distribution_list"]   = distribution_list
     handlers["distribution_get"]    = distribution_get
     handlers["distribution_edit"]   = distribution_edit

