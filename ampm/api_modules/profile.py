#!/usr/bin/python

import base_module
import pprint


class Profile(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["profile_list", "profile_get"]

    def profile_list(self):
        return self.server.profile_list(self.token,{})

    def profile_get(self, id):
        return self.server.profile_get(self.token, {'id': id})

api_class = Profile
