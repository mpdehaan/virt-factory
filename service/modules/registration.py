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

import authentication
import config
import machine
import regtoken
import web_svc


import logging
import os
import threading
import time
import traceback



class Registration(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"register_new_machine": self.new_machine,
                        "register_associate_machine": self.associate}
        web_svc.AuthWebSvc.__init__(self)
        self.auth = authentication.Authentication()

    def new_machine(self, token):
        failed_auth = False
        try:
            self.auth.token_check(token)
        except TokenExpiredException:
            failed_auth = True
        except TokenInvalidException:
            failed_auth = True

        # check the regtoken
        if failed_auth:
            regtoken_obj = regtoken.RegToken()
            # this should raise exceptions if anything fails
            regtoken_obj.check(token)

        # if we get here, we should be authenticated to register

        machine_obj = machine.Machine()
        return machine_obj.new(token)

    def associate(self, token, machine_id, ip_addr, mac_addr, image_id=None):
        machine_obj = machine.Machine()
        return machine_obj.associate(token, machine_id, ip_addr, mac_addr, image_id)


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
