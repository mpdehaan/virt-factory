#!/usr/bin/python

import base_module
import pprint


class Machine(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["machine_add", "machine_list", "machine_get_by_hostname"]

    def machine_add(self, data):
        return self.server.machine_add(self.token, data)

    def machine_list(self):
        return self.server.machine_list(self.token,{})

    def machine_get_by_hostname(self, hostname):
        return self.server.machine_get_by_hostname(self.token, {'hostname':hostname})

api_class = Machine
