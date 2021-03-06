#!/usr/bin/python

import base_module
import pprint


class Deployment(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["deployment_list",
                        "deployment_get",
                        "deployment_add",
                        "deployment_get_by_mac",
                        "deployment_get_by_hostname",
                        "deployment_pause",
                        "deployment_unpause",
                        "deployment_start",
                        "deployment_stop",
                        "deployment_shutdown",
                        "deployment_destroy",
                        "deployment_list"]
                     

    def deployment_pause(self,guest_id):
        return self.server.deployment_pause(self.token, {'id' : guest_id})

    def deployment_unpause(self, guest_id):
        return self.server.deployment_unpause(self.token, {'id' : guest_id})

    def deployment_shutdown(self, guest_id):
        return self.server.deployment_shutdown(self.token, {'id' : guest_id})

    def deployment_destroy(self, guest_id):
        return self.server.deployment_destroy(self.token, {'id' : guest_id})

    def deployment_start(self, guest_id):
        return self.server.deployment_start(self.token, {'id': guest_id})

    def deployment_list(self):
        return self.server.deployment_list(self.token,{})

    def deployment_get_by_mac(self, guest):
        return self.server.deployment_get_by_mac_address(self.token, {'mac_address': guest})

    def deployment_get_by_hostname(self, guest):
        return self.server.deployment_get_by_hostname(self.token, {'hostname': guest})

    def deployment_get(self, guest_id):
        return self.server.deployment_get(self.token, {'id':guest_id})

    def deployment_add(self, machine_id, profile_id, guest_name=None):
        data =  {"machine_id": machine_id,
                 "profile_id": profile_id}
        return self.server.deployment_add(self.token, data)

    

api_class = Deployment
