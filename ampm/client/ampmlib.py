#!/usr/bin/python

# module for ampm functionality


#import logger
#logger.logfilepath = "/var/log/ampm/ampm.log"

import module_loader

from rhpl.translate import _, N_, textdomain, utf8
I18N_DOMAIN = "ampm"


import distutils
import getopt
import os
import socket
import sys
import xmlrpclib


#MODULE_PATH="modules/"
#sys.path.insert(0, MODULE_PATH)
#modules = module_loader.load_modules(module_path=MODULE_PATH)
#print modules

#print sys.path
from client import config
from api_modules import auth
from api_modules import machine
from api_modules import deployment
from api_modules import profile

class Server(xmlrpclib.ServerProxy):
    def __init__(self, url=None):
        xmlrpclib.ServerProxy.__init__(self, url)


# class to handle storing, reading, updating, etc login info
# client side
class AuthInfo(object):
    def __init__(self):
        self.username = None
        self.password = None
        self.token = None
        self.token_file = os.path.expanduser("~/.ampm_token")

    def read_token(self):
        try:
            token = open(self.token_file, "r").readline().strip()
        except:
            raise
        self.token = token
        
    def write_token(self):
        f = open(self.token_file, "w")
        f.write(self.token)
        f.close()
        

# yes, having a class called Api is lame. But this is freaking
# rpc folks. Pretending you are dealing with real objects will
# just lead to pain and bitterness
class Api(object):
    def __init__(self, url=None, username=None, password=None):
        self.url = url
        self.server = Server(url)
        self.username = username
        self.password = password

        self.auth_obj = AuthInfo()
        self.modules = {}
        self.api_classes = {}
        self.api_methods = {}
        

        # FIXME: auto-dynamafy this module/method stuff
        for module in [auth, machine, deployment, profile]:
            self.api_classes[module] = module.api_class()

        for api_class in self.api_classes.keys():
            methods = self.api_classes[api_class].methods
            for method in methods:
                # for now we are going to pretend every nethod has a unique name
                self.api_methods[method] = api_class

    def __getattr__(self, attr):
        self.login()
        if attr in self.api_methods:
            obj = self.api_methods[attr].api_class(server=self.server,
                                                   token=self.token)
            return getattr(obj,attr)
        else:
            raise AttributeError, attr

    # most of the methods in this class are just wrappers around
    # xmlrpc calls

    def login(self):
        

        try:
            self.token = self.server.user_login(self.username, self.password)[1]['data']
        except:
            # FIXME: fancy error handling here later
            raise

        


if __name__ == "__main__":

    # test stuff
    ai = AuthInfo()
    blip = "sdfjadflaksfi9q349wjeruifhs498ryw43ghfsreg"
    ai.token = blip
    ai.write_token()
    ai.read_token()
    print ai.token
    print blip
    if ai.token != blip:
        print "something butestededededicated"
