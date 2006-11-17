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


import time
from codes import *
from errors import *
import baseobj

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
        self.id               = self.load(args,"id",-1)
        self.name             = self.load(args,"name",-1)
        self.version          = self.load(args,"version",-1)
        self.filename         = self.load(args,"filename",-1)
        self.specfile         = self.load(args,"specfile",-1)

    def to_datastruct(self):
        """
        Serialize the object for transmission over WS.
        """
        return {
            "id"              : self.id,
            "name"            : self.name,
            "version"         : self.version,
            "filename"        : self.filename,
            "specfile"        : self.specfile
        }

    def validate(self,operation):
        """
        Cast variables appropriately and raise InvalidArgumentException(["name of bad arg","..."])
        if there are any problems.  Note that validation is operation specific, for instance
        there is no ID for an "add" command because the add command generates the ID.

        Note that getting python exception errors during a cast here is technically good enough
        to prevent GIGO, but really InvalidArgumentsExceptions should be raised.  That's what
        we want.

        NOTE: API currently gives names of invalid fields but does not list reasons.  
        i.e. (FALSE, INVALID_ARGUMENTS, ["foo,"bar"].  By making the 3rd argument a hash
        it could, but these would also need to be codes.  { "foo" : OUT_OF_RANGE, "bar" : ... }
        Up for consideration, but probably not needed at this point.  Can be added later. 
        """
        # FIXME
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def image_add(websvc,args):
     """
     Create a image.  args should contain all fields except ID.
     """
     u = Image.produce(args,OP_ADD)
     u.id = int(time.time())
     st = """
     INSERT INTO images (id,iname,version,filename,specfile)
     VALUES (:id,:name,:version,:filename,:specfile)
     """
     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()
     return success(u.id)

def image_edit(websvc,args):
     """
     Edit a image.  args should contain all fields that need to
     be changed.
     """
     u = Image.produce(args,OP_EDIT) # force validation
     st = """
     UPDATE images 
     SET images.name=:name
     images.version=:version,
     images.filename=:filename,
     images.specfile=:specfile
     WHERE images.id=:id
     """
     websvc.cursor.execute(st, u.to_datastruct())
     websvc.connection.commit()
     return success(u.to_datastruct())

def image_delete(websvc,args):
     """
     Deletes a image.  The args must only contain the id field.
     """
     u = Image.produce(args,OP_DELETE) # force validation
     st = """
     DELETE FROM images WHERE images.id=:id
     """
     websvc.cursor.execute(st, { "id" : u.id })
     websvc.connection.commit()
     # FIXME: failure based on existance
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
     SELECT id,name,version,filename,specfile
     FROM users LIMIT ?,?
     """ 
     results = websvc.cursor.execute(st, (offset,limit))
     results = websvc.cursor.fetchall()
     images = []
     for x in results:
         data = {         
            "id"        : x[0],
            "name"      : x[1],
            "version"   : x[2],
            "filename"  : x[3],
            "specfile"  : x[4]
         }
         images.append(Image.produce(data).to_datastruct())
     return success(images)

def image_get(websvc,args):
     """
     Return a specific image record.  Only the "id" is required in args.
     """
     u = Image.produce(args,OP_GET) # force validation
     st = """
     SELECT id,name,version,filename,specfile
     FROM images WHERE id=?
     """
     websvc.cursor.execute(st,{ "id" : u.id })
     x = websvc.cursor.fetchone()
     if x is None:
         raise InvalidArgumentsException(["id"])
     data = {
            "id"       : x[0],
            "name"     : x[1],
            "version"  : x[2],
            "filename" : x[3],
            "specfile" : x[4],
     }
     return success(Image.produce(data).to_datastruct())

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """
     handlers["image_add"]    = image_add
     handlers["image_delete"] = image_delete
     handlers["image_list"]   = image_list
     handlers["image_get"]    = image_get
     handlers["image_edit"]   = image_edit

