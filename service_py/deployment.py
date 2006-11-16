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
import base64
from sqlalchemy import *
from codes import *
from errors import *
import baseobj

import image
import machine

class Deployment(baseobj.BaseObject):

    def _produce(clss, args,operation=None):
        """
        Factory method.  Create a object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the object.
        """
        self = Deployment()
        self.from_datastruct(args)
        self.validate(operation)
        return self
    produce = classmethod(_produce)

    def from_datastruct(self,args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  
        """
        self.id          = self.load(args,"id",-1)
        self.machine_id  = self.load(args,"machine_id",-1)
        self.image_id    = self.load(args,"image_id",-1)
        self.state       = self.load(args,"state",-1)

    def to_datastruct(self):
        """
        Serialize the object for transmission over WS.
        """
        return {
            "id"          : self.id,
            "machine"     : self.machine.to_datastruct(),
            "image"       : self.image.to_datastruct(),
            "state"       : self.middle,
        }

    def validate(self,operation):
        """
        Clean up input and throw exceptions on bad args.
        """
        # FIXME
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def make_table(meta):
     """
     This method is called to hand the table object to sqlalchemy. SQLA can actually
     create the table but for upgrade reasons, we're letting it just read the metadata.
     """
     tbl = Table('deployments', meta, autoload=True)
     map = mapper(Deployment, tbl)
     map.add_property('machine_id', relation(machine.Machine))
     map.add_property('image_id', relation(image.Image))
     return tbl
   
def deployment_add(session,args):
     """
     Create a deployment.
     """
     dep = Deployment.produce(args,OP_ADD) # force validation
     dep.id = int(time.time()) # FIXME (?)
     return deployment_save(session,dep,args)

def deployment_edit(session,args):
     """
     Edit a deployment
     """
     # FIXME: allow the password field to NOT be sent, therefore not
     #        changing it.  (OR) just always do XMLRPC/HTTPS and use a 
     #        HTML password field.  Either way.  (We're going to be
     #        wanting HTTPS anyhow).
     temp_dep = Deployment.produce(args,OP_EDIT) # force validation
     query = session.query(Deployment)
     dep = query.get_by(Deployment.c.id.in_(temp_dep.id))
     if dep is None:
        raise NoSuchObjectException()
     return deployment_save(session,dep,args)

def deployment_save(session,dep,args):
     """
     Helper method used by _add and _save.
     """
     # validation already done in methods calling this helper
     dep.id = args["id"]
     # FIXME: doesn't look right with join stuff (?)
     dep.machine_id = args["machine"]
     dep.image_id   = args["image"]
     dep.state = args["state"]
     session.save(dep)
     session.flush()
     ok = dep in session
     if not ok:
         raise InternalErrorException()
     return success()

def deployment_delete(session,args):
     """
     Deletes a deployment.  The args must only contain the id field.
     """
     # FIXME: doesn't apply to this module but does for others.
     # when deleting machines and images, think about orphan deployments
     temp_dep = Deployment.produce(args,OP_DELETE) # force validation
     query = session.query(Deployment)
     dep = query.get_by(Deployment.c.id.in_(temp_dep.id))
     if dep is None:
        return result(ERR_NO_SO_OBJECT)
     session.delete(dep)
     session.flush()
     ok = not dep in session
     if not ok:
         raise InternalErrorException()
     return success()

def deployment_list(session,args):
     """
     Return a list of deployments. 
     """
     # no validation required
     query = session.query(Deployment)
     sel = query.select()
     list = [x.to_datastruct() for x in sel]
     return success(list)

def deployment_get(session,args):
     """
     Return a specific dep record.  Only the "id" is required in args.
     """
     temp_dep = Deployment.produce(args,OP_GET) # force validation
     query = session.query(Deployment)
     dep = query.get_by(Deployment.c.id.in_(temp_dep.id))
     if dep is None:
        raise NoSuchObjectException()
     return success(dep.to_datastruct())

def register_rpc(handlers):
     """
     This adds RPC functions to the global list of handled functions.
     """
     handlers["deployment_add"]    = deployment_add
     handlers["deployment_delete"] = deployment_delete
     handlers["deployment_list"]   = deployment_list
     handlers["deployment_get"]    = deployment_get
     handlers["deployment_edit"]   = deployment_edit

