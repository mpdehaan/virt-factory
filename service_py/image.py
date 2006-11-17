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
        self = Image()
        self.from_datastruct(args)
        self.validate(operation)
        return self
    produce = classmethod(_produce)

    def from_datastruct(self,args):
        self.id             = self.load(args,"id",-1)
        self.name           = self.load(args,"name",-1)
        self.version        = self.load(args,"version",-1)
        self.filename       = self.load(args,"filename",-1)
        self.specfile       = self.load(args,"specfile",-1)


    def to_datastruct(self):
        return {
            "id"             : self.id,
            "name"           : self.name,
            "version"        : self.version,
            "specfile"       : self.specfile,
            "filename"       : self.filename
        }

    def validate(self, operation):
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def image_add(session,args):
     image = Image.produce(args,OP_ADD) # force validation
     image.id = int(time.time()) # FIXME (?)
     return image_save(session,image,args)

def image_edit(session,args):
     temp_image = Image.produce(args,OP_EDIT) # force validation
     query = session.query(Image)
     image = query.get_by(Image.c.id.in_(temp_image.id))
     if image is None:
        raise NoSuchObjectException()
     return image_save(session,image,args)

def image_save(session,image,args):
     # validation already done in methods calling this helper
     image.name = args["name"]
     image.version = args["version"]
     image.filename = args["filename"]
     image.specfile = args["specfile"]
     # FIXME: we'd want to do validation here (actually in the Image class) 
     session.save(image)
     session.flush()
     ok = image in session
     if not ok:
         raise InternalErrorException()
     return success()

def image_delete(session,args):
     temp_image = Image.produce(args,OP_DELETE) # force validation
     query = session.query(Image)
     image = query.get_by(Image.c.id.in_(temp_image.id))
     if image is None:
        return result(ERR_NO_SO_OBJECT)
     session.delete(image)
     session.flush()
     ok = not image in session
     if not ok:
         raise InternalErrorException()
     return success()

def image_list(session,args):
     # no validation required
     query = session.query(Image)
     sel = query.select()
     list = [x.to_datastruct() for x in sel]
     return success(list)

def image_get(session,args):
     temp_image = Image.produce(args,OP_GET) # force validation
     query = session.query(Image)
     image = query.get_by(Image.c.id.in_(temp_image.id))
     if image is None:
        raise NoSuchObjectException()
     return success(image.to_datastruct())

def register_rpc(handlers):
     handlers["image_add"]    = image_add
     handlers["image_delete"] = image_delete
     handlers["image_list"]   = image_list
     handlers["image_get"]    = image_get
     handlers["image_edit"]   = image_edit

