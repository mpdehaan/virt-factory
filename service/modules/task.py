"""
ShadowManager backend code for task (background ops) framework.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import baseobj
from codes import *

import machine
import deployment
import user

#import distribution
#import provisioning
import web_svc

import os
import threading
import traceback
import time

#------------------------------------------------------

class TaskData(baseobj.BaseObject):

    FIELDS = [ "id", "user_id", "operation", "parameters", "state", "time" ] 

    def _produce(klass, profile_args,operation=None):
        """
        Factory method.  Create an object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the profile object.
        """

        self = TaskData()
        self.from_datastruct(profile_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,args):
        """
        Deserialize the object from input
        """
        return self.deserialize(args) # ,self.FIELDS)

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
 
        if operation in [OP_ADD]:

            if self.operation not in VALID_TASK_OPERATIONS:
                invalid_fields["operation"] = REASON_RANGE
        
        if operation in [OP_ADD, OP_EDIT]:

            if self.state not in VALID_TASK_STATES:
                invalid_fields["state"] = REASON_RANGE

        if len(invalid_fields) > 0:
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


class Task(web_svc.AuthWebSvc):
    
   DB_SCHEMA = {
       "table" : "tasks",
       "fields" : TaskData.FIELDS,
       "add"   : [ "user_id", "operation", "parameters", "state", "time" ],
       "edit"  : [ "state" ]
    }

   def __init__(self):
       """
       Constructor.  Add methods that we want registered.
       """
       
       self.methods = {
           "task_add"    : self.add,
           "task_edit"   : self.edit,
           "task_list"   : self.list,
           "task_get"    : self.get,
           "task_delete" : self.delete
           }
       web_svc.AuthWebSvc.__init__(self)

       # FIXME: could go in the baseclass...
       self.db.db_schema = self.DB_SCHEMA

   def add(self, token, args):
       """
       Create a profile.  profile_args should contain all fields except ID.
       """
       
       u = TaskData.produce(args,OP_ADD) # force validation
       data = u.to_datastruct()
       data["time"] = time.time()
            
 
       # no longer used...
       # self.db.validate_foreign_key(u.machine_id,    'machine_id',    machine.Machine())
       # self.db.validate_foreign_key(u.deployment_id, 'deployment_id', deployment.Deployment())
       
       # FIXME: same note as above
       # self.db.validate_foreign_key(u.user_id,       'user_id',       user.User())

       return self.db.simple_add(data)


   def edit(self, token, args):
       """
       Edit object.  Args should contain all fields that need to be changed.
       """
       
       u = TaskData.produce(args,OP_EDIT) # force validation
       return self.db.simple_edit(u.to_datastruct())


   def delete(self, token, args):
       """
       Deletes an object.  args must only contain the id field.
       """
       
       u = TaskData.produce(args,OP_DELETE) # force validation
       return self.db.simple_delete(u.to_datastruct())
   

   def list(self, token, args):
       """
       Return a list of objects.  The args list is currently *NOT*
       used.  Ideally we need to include LIMIT information here for
       GUI pagination when we start worrying about hundreds of systems.
       """
       
       return self.db.simple_list(args)


   def get(self, token, args):
       """
       Return a specific record.  Only the "id" is required in args.
       """
       
       u = TaskData.produce(args, OP_GET) # validate
       return self.db.simple_get(u.to_datastruct())
 
methods = Task()
register_rpc = methods.register_rpc

