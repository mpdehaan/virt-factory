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
import image

import logging
import os
import threading
import time
import traceback



class Registration(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"register": self.register, }
        web_svc.AuthWebSvc.__init__(self)
        self.auth = authentication.Authentication()

    def __check_auth(self, token):
        print "__check_auth"
        failed_auth = False
        try:
            self.auth.token_check(token)
        except TokenExpiredException:
            failed_auth = True
        except TokenInvalidException:
            failed_auth = True

        # check the regtoken
        if failed_auth:
            print "making the regtoken..."
            regtoken_obj = regtoken.RegToken()
            # this should raise exceptions if anything fails
            print "debug: checking regtoken..."
            regtoken_obj.check(token)
            
    def new_machine(self, token):
        self.__check_auth(token)

        machine_obj = machine.Machine()
        return machine_obj.new(token)

    def register(self, token, hostname, ip_addr, mac_addr, image_name):
        self.__check_auth(token)
        
        machine_obj = machine.Machine()
        results = machine_obj.db.simple_list({}, { "mac_address" : mac_addr })
        if results.error_code != 0:
            return results
        if len(results.data) != 0:
            print "simple machine query"
            machine_id =  results.data[0]["id"]
            print "existing machine id = %s" % machine_id
        else:
            results = machine_obj.new(token)
            machine_id = results.data 
            print "new machine id = %s" % machine_id

        image_id = 0

        # see if there is an image id for the token.  this does not work
        # for usernames and passwords.
        regtoken_obj = regtoken.RegToken()
        regtoken_obj.db.simple_list({}, { "token" : token })
        if results.error_code != 0 and len(results.data) != 0:
            image_id = results.data[0]["image_id"]

        if image_id == 0 and image_name != "":
            # no image ID found for token, try a name lookup
            image_obj = image.Image()
            images = image_obj.db.simple_list({}, { "name" : image_name })
            if images.error_code != 0 and len(images.data) != 0:
                image_id = results.data[0]["id"]

        print "calling associate with machine_id: ", machine_id
        return machine_obj.associate(token, machine_id, hostname, ip_addr, mac_addr, image_id)


methods = Registration()
register_rpc = methods.register_rpc
