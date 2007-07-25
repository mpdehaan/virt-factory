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
        (retcode, data) = self.server.machine_list(self.token,{})
        pprint.pprint(data)
        for machine in data['data']:
            if machine['id'] == -1:
                continue
            print "hostname: %s id: %s profile_name: %s" % (machine['id'], machine['hostname'], machine['profile']['name'])
#            print machine['id']
#            print machine['hostname']
#            print machine['profile']['name']

api_class = Machine
