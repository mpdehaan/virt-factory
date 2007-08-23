#!/usr/bin/python

import base_module
import pprint

class Task(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["task_list",]

    def task_list(self):
        return self.server.task_list(self.token, {})


api_class = Task
