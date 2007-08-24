#!/usr/bin/python

import base_module
import pprint


class User(base_module.BaseModule):
    def __init__(self, server=None, token=None):
        self.token = token
        self.server = server
        base_module.BaseModule.__init__(self)
        self.methods = ["user_list", "user_add", "user_delete"]

    def user_list(self):
        return self.server.user_list(self.token, {})

    def user_add(self, username,
                    password, first,
                    last,description, email, middle=None):
        data = {'username': username,
                'password': password,
                "first": first,
                'last': last,
                'description': description,
                'email': email}
        if middle:
            data['middle'] = middle

        return self.server.user_add(self.token, data)

    def user_delete(self, user_id):
        return self.server.user_delete(self.token, {'id':user_id})
        
                                                 
api_class = User
