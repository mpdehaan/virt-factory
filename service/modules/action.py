"""
ShadowManager backend code for actions framework.

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

#import distribution
#import provisioning
import web_svc

import os
import threading
import traceback

#------------------------------------------------------

class ActionData(baseobj.BaseObject):

    FIELDS = [ "id", "machine_id", "deployment_id", "user_id", "operation", "parameters", "state" ] 

    def _produce(klass, image_args,operation=None):
        """
        Factory method.  Create an object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the image object.
        """

        self = ActionData()
        self.from_datastruct(image_args)
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
 
        if operation in [OP_ADD, OP_EDIT]:

            if self.operation not in VALID_ACTION_OPERATIONS:
                invalid_fields["operation"] = REASON_RANGE

            if self.state not in VALID_ACTION_STATES:
                invalid_fields["state"] = REASON_RANGE

        if len(invalid_fields) > 0:
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


class Action(web_svc.AuthWebSvc):
    
   DB_SCHEMA = {
       "table" : "actions",
       "fields" : ActionData.FIELDS,
       "add"   : [ "machine_id", "deployment_id", "user_id", "operation", "parameters", "state" ],
       "edit"  : [ "state" ]
    }

   def __init__(self):
       """
       Constructor.  Add methods that we want registered.
       """
       
       self.methods = {
           "action_add"    : self.add,
           "action_list"   : self.list,
           "action_get"    : self.get,
           "action_delete" : self.delete
           }
       web_svc.AuthWebSvc.__init__(self)

       # FIXME: could go in the baseclass...
       self.db.db_schema = self.DB_SCHEMA

   def add(self, token, args):
       """
       Create a image.  image_args should contain all fields except ID.
       """
       
       u = ActionData.produce(args,OP_ADD)
       
       self.db.validate_foreign_key(u.machine_id,    'machine_id',    machine.Machine())
       self.db.validate_foreign_key(u.deployment_id, 'deployment_id', deployment.Deployment())
       self.db.validate_foreign_key(u.user_id,       'user_id',       user.User())
       
       return self.db.simple_add(ActionData,args)


   def edit(self, token, args):
       """
       Edit object.  Args should contain all fields that need to be changed.
       """
       
       u = ActionData.produce(image_args,OP_EDIT) # force validation
       return self.db.simple_edit(ActionData,args)


   def delete(self, token, args):
       """
       Deletes an object.  args must only contain the id field.
       """
       
       u = ActionData.produce(args,OP_DELETE) # force validation
       return self.db.simple_delete(ActionData,args)
   

   def list(self, token, args):
       """
       Return a list of objects.  The args list is currently *NOT*
       used.  Ideally we need to include LIMIT information here for
       GUI pagination when we start worrying about hundreds of systems.
       """
       
       return self.db.simple_list(args, self.DB_SCHEMA['fields'], self.DB_SCHEMA['table'])


   def get(self, token, args):
       """
       Return a specific record.  Only the "id" is required in args.
       """
       
       u = ActionData.produce(args, OP_GET) # validate
       return self.db.simple_get(ActionData, args)
   

methods = Action()
register_rpc = methods.register_rpc

