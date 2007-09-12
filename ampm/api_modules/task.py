#!/usr/bin/python

import base_module
import pprint

class Task(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["task_list","task_delete"]

    def task_list(self, where_args={}):
        return self.server.task_list(self.token, {}, where_args)

    def task_delete(self, task_id):
        return self.server.task_delete(self.token, {'id':task_id})

api_class = Task
