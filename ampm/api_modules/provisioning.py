#!/usr/bin/python

import base_module
import pprint


class Provisioning(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["provisioning_init"]

    def provisioning_init(self):
        return self.server.provisioning_init(self.token,{})

api_class = Provisioning
