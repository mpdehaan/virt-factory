#!/usr/bin/python

import base_module
import pprint


class Machine(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["machine_list"]

    def machine_list(self):
        return self.server.machine_list(self.token,{})

api_class = Machine
