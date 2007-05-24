#!/usr/bin/python
"""
Virt-factory backend code for task (background ops) framework.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

from server.codes import *
from server import db

import baseobj
import web_svc

class Task(web_svc.AuthWebSvc):

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
   

    def add(self, token, args):
         """
         Create a task.
         @param args: A dictionary of task attributes.
             - user_id
             - action_type
             - machine_id
             - deployment_id
             - state
         @type args: dict
         """
         optional = ()
         required = ('user_id', 'action_type', 'machine_id', 'deployment_id', 'state')
         validator = FieldValidator(args)
         validator.verify_required(required)
         validator.verity_enum('state', VALID_TASK_STATES)
         validator.verity_enum('action_type', VALID_TASK_STATES)
         session = db.open_session()
         try:
             task = db.Task()
             for key in (required):
                 setattr(task, key, args.get(key, None))
             session.save(task)
             session.flush()
             return success(task.id)
         finally:
             session.close()


    def edit(self, token, args):
         """
         Edit a task.
         @param args: A dictionary of task attributes.
             - user_id
             - action_type
             - machine_id
             - deployment_id
             - state
         @type args: dict
         """
         required = ('id')
         optional = ('user_id', 'action_type', 'machine_id', 'deployment_id', 'state')
         validator.verify_required(required)
         validator.verity_enum('state', VALID_TASK_STATES)
         validator.verity_enum('action_type', VALID_TASK_STATES)
         session = db.open_session()
         try:
             taskid = args['id']
             task = session.get(db.Task, taskid)
             if task is None:
                 raise NoSuchObjectException(comment=taskid)
             for key in (optional):
                 setattr(task, key, args.get(key, None))
             session.save(task)
             session.flush()
             return success()
         finally:
             session.close()


    def delete(self, token, args):
         """
         Deletes a task.
         @param args: A dictionary of task attributes.
             - id
         @type args: dict
         """
         required = ('id',)
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         try:
             taskid = args['id']
             task = session.get(db.Task, taskid)
             if task is None:
                 raise NoSuchObjectException(comment=taskid)
             session.delete(task)
             session.flush()
             return success()
         finally:
             session.close()
   

    def list(self, token, args):
         """
         Get all tasks.
         @param args: A dictionary of attributes.
         @type args: dict
         @return: A list of tasks.
         @rtype: dictionary
             - id
             - user_id
             - action_type
             - machine_id
             - deployment_id
             - state
             - time
         # FIXME: implement paging
         """
         session = db.open_session()
         try:
             result = []
             query = session.query(db.Task)
             for task in query.select():
                 result.append(self.__taskdata(task))
             return success(result)
         finally:
             session.close()


    def get(self, token, args):
         """
         Get a task by id.
         @param args: A dictionary of task attributes.
             - id
         @type args: dict
         """
         required = ('id',)
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         try:
             taskid = args['id']
             task = session.get(db.Task, taskid)
             if task is None:
                 raise NoSuchObjectException(comment=task)
             return success(self.__taskdata(task))
         finally:
             session.close()


    def __taskdata(self, task):
        result =\
            {'id':task.id,
             'user_id':task.user_id,
             'action_type':task.action_type,
             'machine_id':task.machine_id,
             'deployment_id':task.deployment_id,
             'state':task.state,
             'time':task.time}
        return FieldValidator.prune(result)
 
methods = Task()
register_rpc = methods.register_rpc

