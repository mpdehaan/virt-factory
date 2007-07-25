#!/usr/bin/python

import base_module
import pprint


class Deployment(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["deployment_list", "deployment_get"]

    def deployment_list(self):
        return self.server.deployment_list(self.token,{})

    def deployment_get(self, deployment):
        return self.server.deployment_get_by_mac_address(self.token, {'mac_address': deployment})

api_class = Deployment
