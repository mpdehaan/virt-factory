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
import time 
from fieldvalidator import FieldValidator
import web_svc

class Task(web_svc.AuthWebSvc):

    def __init__(self):
       """
       Constructor.  Add methods that we want registered.
       """       
       self.methods = {
           "task_add"               : self.add,
           "task_add_by_tag"        : self.add_by_tag,
           "task_edit"              : self.edit,
           "task_list"              : self.list,
           "task_get"               : self.get,
           "task_delete"            : self.delete,
           "task_get_by_machine"    : self.get_by_machine,
           "task_get_by_deployment" : self.get_by_deployment
           }
       web_svc.AuthWebSvc.__init__(self)
   

    def add(self, token, args):
        """
        Create a task.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of task attributes.
            - user_id
            - action_type
            - machine_id
            - deployment_id
            - state
        @type args: dict
        @raise SQLException: On database error
        """
        optional = ()
        required = ('user_id', 'action_type', 'machine_id', 'deployment_id', 'state')
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_enum('state', VALID_TASK_STATES)
        validator.verify_enum('action_type', VALID_TASK_OPERATIONS)
        session = db.open_session()
        try:
            task = db.Task()
            task.update(args)
            session.save(task)
            session.flush()
            return success(task.id)
        finally:
            session.close()


    def add_by_tag(self, token, args):
        """
        Create a task by tag. A separate task will be added
        for each deployment with this tag
        @param token: A security token.
        @type token: string
        @param args: A dictionary of task attributes.
            - user_id
            - action_type
            - tag
            - state
        @type args: dict
        @raise SQLException: On database error
        """
        optional = ()
        required = ('user_id', 'action_type', 'tag', 'state')
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_enum('state', VALID_TASK_STATES)
        validator.verify_enum('action_type', VALID_TASK_OPERATIONS)
        deployments = deployment.Deployment().get_by_tag(None, args)
        if deployments.error_code != 0:
            return deployments
        
        result = []
        for deployment in deployments.data:
            args["deployment_id"]=deployment["id"]
            args["machine_id"]=deployment["machine_id"]
            id = self.add(None, args)
            if id.error_code != 0:
                return id
            result.append(id.data)
        return success(id)


    def edit(self, token, args):
        """
        Edit a task.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of task attributes.
            - id
            - state  (optional)
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        optional = ('state',)
        filter_fields = ('id', 'user_id', 'action_type', 'machine_id', 'deployment_id')
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_enum('state', VALID_TASK_STATES)
        validator.verify_enum('action_type', VALID_TASK_STATES)
        session = db.open_session()
        try:
            task = db.Task.get(session, args['id'])
            task.update(args, filter_fields)
            session.save(task)
            session.flush()
            return success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Deletes a task.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of task attributes.
            - id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.Task.delete(session, args['id'])
            return success()
        finally:
            session.close()
   

    def list(self, token, args):
        """
        Get all tasks.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of task attributes.
        @type args: dict
           - offset (optional)
           - limit (optional)
        @return: A list of tasks.
        @rtype: [dict,]
            - id
            - user_id
            - action_type
            - machine_id
            - deployment_id
            - state
        @raise SQLException: On database error
        """
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for task in db.Task.list(session, offset, limit):
                result.append(self.expand(task))
            return success(result)
        finally:
            session.close()


    def get_by_machine(self, token, args):
        """
        Returns a list of tasks for a given host
        """
        required = ('machine_id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            machine_id = args['machine_id']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Task).limit(limit).offset(offset)
            for task in query.select_by(machine_id = machine_id):
                result.append(self.expand(task))
            return success(result)
        finally:
            session.close()

    def get_by_deployment(self, token, args):
        """
        Returns a list of tasks for a given guest
        """
        required = ('deployment_id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            deployment_id = args['deployment_id']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Task).limit(limit).offset(offset)
            for task in query.select_by(deployment_id = deployment_id):
                result.append(self.expand(task))
            return success(result)
        finally:
            session.close()

    def get(self, token, args):
        """
        Get a task by id.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of task attributes.
            - id
        @type args: dict
            - id
            - user_id
            - action_type
            - machine_id
            - deployment_id
            - state
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            task = db.Task.get(session, args['id'])
            return success(self.expand(task))
        finally:
            session.close()


    def expand(self, task):
        result = task.get_hash()
        result['user'] = task.user.get_hash()
        result['machine'] = task.machine.get_hash()
        result['deployment'] = task.deployment.get_hash()
        result['time'] = time.mktime(task.time.timetuple())
        return result
        
 
 
methods = Task()
register_rpc = methods.register_rpc

