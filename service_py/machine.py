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

def make_table(meta):
    tbl = Table('machines', meta, autoload=True)
    mapper(Machine, tbl)
    return tbl

class Machine(baseobj.BaseObject):

    def _produce(clss, args,operation=None):
        self = Machine()
        self.from_datastruct(args)
        self.validate(operation)
        return self
    produce = classmethod(_produce)

    def from_datastruct(self,args):
        self.id           = self.load(args,"id",-1)
        self.machine      = self.load(args,"machine",-1)
        self.architecture = self.load(args,"architecture",-1)
        self.processors   = self.load(args,"processor_speed",-1)
        self.processors   = self.load(args,"processor_count",-1)
        self.memory       = self.load(args,"memory",-1)


    def to_datastruct(self):
        return {
            "id"                : self.id,
            "machine"           : self.machine,
            "architecture"      : self.architecture,
	    "processor_speed"   : self.processors,
            "processor_count"   : self.processors,
            "memory"            : self.memory
        }

    def validate(self, operation):
        # FIXME
        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            self.id = int(self.id)

def machine_add(session,args):
     machine = Machine.produce(args,OP_ADD) # force validation
     machine.id = int(time.time()) # FIXME (?)
     return machine_save(session,machine,args)

def machine_edit(session,args):
     temp_machine = Machine.produce(args,OP_EDIT) # force validation
     query = session.query(Machine)
     machine = query.get_by(Machine.c.id.in_(temp_machine.id))
     if machine is None:
        raise NoSuchObjectException()
     return machine_save(session,machine,args)

def machine_save(session,machine,args):
     # validation already done in methods calling this helper
     machine.architecture = args["architecture"]
     machine.processor_speed = args["processor_speed"]
     machine.processor_count = args["processor_count"]
     machine.address = args["address"]
     machine.memory = args["memory"]
     # FIXME: we'd want to do validation here (actually in the Machine class) 
     session.save(machine)
     session.flush()
     ok = machine in session
     if not ok:
         raise InternalErrorException()
     return success()

def machine_delete(session,args):
     temp_machine = Machine.produce(args,OP_DELETE) # force validation
     query = session.query(Machine)
     machine = query.get_by(Machine.c.id.in_(temp_machine.id))
     if machine is None:
        return result(ERR_NO_SO_OBJECT)
     session.delete(machine)
     session.flush()
     ok = not machine in session
     if not ok:
         raise InternalErrorException()
     return success()

def machine_list(session,args):
     # no validation required
     query = session.query(Machine)
     sel = query.select()
     list = [x.to_datastruct() for x in sel]
     return success(list)

def machine_get(session,args):
     temp_machine = Machine.produce(args,OP_GET) # force validation
     query = session.query(Machine)
     machine = query.get_by(Machine.c.id.in_(temp_machine.id))
     if machine is None:
        raise NoSuchObjectException()
     return success(machine.to_datastruct())

def register_rpc(handlers):
     handlers["machine_add"]    = machine_add
     handlers["machine_delete"] = machine_delete
     handlers["machine_list"]   = machine_list
     handlers["machine_get"]    = machine_get
     handlers["machine_edit"]   = machine_edit

