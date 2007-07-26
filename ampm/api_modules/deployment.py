#!/usr/bin/python

import base_module
import pprint


class Deployment(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["deployment_list", "deployment_get", "deployment_add"]

    def deployment_list(self):
        return self.server.deployment_list(self.token,{})

    def deployment_get_by_mac(self, deployment):
        return self.server.deployment_get_by_mac_address(self.token, {'mac_address': deployment})

    def deployment_get(self, deployment_id):
        return self.server.deployment_get(self.token, {'id':deployment_id})

    def deployment_add(self, machine_id, profile_id, deployment_name=None):
        data =  {"machine_id": machine_id,
                 "profile_id": profile_id}
        return self.server.deployment_add(self.token, data)

    

api_class = Deployment
