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

from codes import *
import baseobj

import config
import web_svc

import logging
import os
import threading
import time
import traceback



class Registration(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"register_add": self.add,
                        "register_test": self.test}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        register a system. Connects an instances with a hostname and mac address
        """
        return 1

    def test(self, token, args):
        print self.token_check(token)
        return 1


methods = Registration()
register_rpc = methods.register_rpc
