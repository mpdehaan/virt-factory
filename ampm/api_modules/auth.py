#!/usr/bin/python

import base_module



class Auth(base_module.BaseModule):
    def __init__(self):
        base_module.BaseModule.__init__(self)
        self.methods = ["login"]

    def login(self, username, password):
        try:
            self.token = self.server.user_login(username, password)
        except:
            # FIXME: fancy error handling here later
            raise

api_class = Auth
