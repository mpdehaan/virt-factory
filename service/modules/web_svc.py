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

from server.codes import *

import baseobj
from server import config_data
from server import db_util
from server import logger

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
        self.__init_log()
        self.__init_db()

    def __init_db(self):
        self.db = db_util.DbUtil()
        
    def __init_log(self):
        # lets see what happens when we c&p the stuff from shadow.py 
        log = logger.Logger()
        self.logger = log.logger
    
    def register_rpc(self, handlers):
        for meth in self.methods:
            handlers[meth] = self.methods[meth]


class AuthWebSvc(WebSvc):
    def __init__(self):
        WebSvc.__init__(self)


