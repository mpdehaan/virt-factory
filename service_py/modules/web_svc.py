#!/usr/bin/python

## ShadowManager backend code.
##
## Copyright 2006, Red Hat, Inc
## Adrian Likins <alikins@redhat.com
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
##

from codes import *

import baseobj
import config_data
import logger

from pysqlite2 import dbapi2 as sqlite

import os
import threading
import time
import traceback


class WebSvc(object):
    def __init__(self):

        config_obj = config_data.Config()
        config_result = config_obj.get()
        self.config = config_result
        self.dbpath = self.config["databases"]["primary"]
        self.__init_log()
        self.__init_sql()

    def __init_sql(self):
        self.connection = self.sqlite_connect()
        self.cursor = self.connection.cursor()
        
    def __init_log(self):
        # lets see what happens when we c&p the stuff from shadow.py 
        log = logger.Logger()
        self.logger = log.logger
    
    def register_rpc(self, handlers):
        for meth in self.methods:
            print meth
            handlers[meth] = self.methods[meth]

    def sqlite_connect(self):
      """Workaround for \"can't connect to full and/or unicode path\" weirdness"""
      
      current = os.getcwd() 
      os.chdir(os.path.dirname(self.dbpath))
      conn = sqlite.connect(os.path.basename(self.dbpath))
      os.chdir(current)
      return conn 


class AuthWebSvc(WebSvc):
    def __init__(self):
        self.tokens = []
        WebSvc.__init__(self)

    def token_check(self, token):
        return 1

    # FIXME: not sure if those code make anysense to me. It seems to be
    # an xmlrpc call, and a local method at the same times. That makes my brain hurt
    def token_check_old(self,token):
       """
       Validate that the token passed in to any method call other than user_login
       is correct, and if not, raise an Exception.  Note that all exceptions are
       caught in dispatch, so methods give failing return codes rather than XMLRPCFaults.
       This is a feature, mainly since Rails (and other language bindings) can better
       grok tracebacks this way.
       """

       if not os.path.exists("/var/lib/shadowmanager/settings"):
            x = MisconfiguredException(comment="/var/lib/shadowmanager/settings doesn't exist")
            return x.to_datastruct()

       self.logger.debug("token check")
       now = time.time()
       for t in self.tokens:
           # remove tokens older than 1/2 hour
           if (now - t[1]) > 1800:
               self.tokens.remove(t)
               return TokenExpiredException().to_datastruct()
           if t[0] == token:
               # update the expiration counter
               t[1] = time.time()
               #return SuccessException()
               return success().to_datastruct()
       return TokenInvalidException().to_datastruct()
    
