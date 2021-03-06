#!/usr/bin/python

## Virt-factory backend code.
##
## Copyright 2006, Red Hat, Inc
## Adrian Likins <alikins@redhat.com>
## Michael DeHaan <mdehaan@redhat.com>
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from server.codes import *

import authentication
import machine
import deployment
import regtoken
import web_svc
import profile

import traceback



class Registration(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"register_system": self.register_system, }
        web_svc.AuthWebSvc.__init__(self)
        self.auth = authentication.Authentication()

    def __check_auth(self, token):
        self.logger.debug("__check_auth")
        failed_auth = False
        try:
            self.auth.token_check(token)
        except TokenExpiredException:
            failed_auth = True
        except TokenInvalidException:
            failed_auth = True

        # check the regtoken
        if failed_auth:
            self.logger.debug("making the regtoken...")
            regtoken_obj = regtoken.RegToken()
            # this should raise exceptions if anything fails
            self.logger.debug("debug: checking regtoken...")
            regtoken_obj.check(token)
            
    def new_machine(self, token):
        self.__check_auth(token)

        machine_obj = machine.Machine()
        return machine_obj.new(token)

    def register_system(self, token, hostname, ip_addr, mac_addr, profile_name, virtual):

        self.__check_auth(token)
        machine_id = None
        
        if virtual:
            self.logger.info("registering a deployment")
            abstract_obj = deployment.Deployment()
        else:
            self.logger.info("registering a machine")
            abstract_obj = machine.Machine()
        self.logger.info("registering against mac address: %s" % mac_addr)
        results = abstract_obj.get_by_mac_address({}, { "mac_address" : mac_addr })
        self.logger.debug("done with mac_address query")
        if results.error_code != 0:
            return results
        if len(results.data) > 0:
            self.logger.info("results = %s" % results)
            abstract_id =  results.data[0]["id"]
            self.logger.info("existing id = %s" % abstract_id)
            if virtual:
               machine_id = results.data[0]["machine_id"]
            else:
               machine_id = results.data[0]["id"]
        else:
            self.logger.debug("no match found for mac: %s" % mac_addr)
            if virtual:
                raise VirtFactoryException(comment="not pre-created")
            # should never happen for virtual machines 
            results = abstract_obj.new(token)
            self.logger.info("results = %s" % results)
            machine_id = abstract_id = results.data 
            self.logger.info("new abstract id = %s" % abstract_id)

        profile_id = None

        # see if there is an profile id for the token.  this does not work
        # for usernames and passwords.
        if token is not None and token != "" and token != "UNSET":
            regtoken_obj = regtoken.RegToken()
            results = regtoken_obj.get_by_token({}, { "token" : "%s" % token })
            if results.error_code != 0 and len(results.data) != 0:
                self.logger.debug("regtoken match from regtoken table")
                profile_id = results.data[0]["profile_id"]

            # if profile id is still None, check the machines table
            if profile_id is not None:
                machine_obj = machine.Machine() 
                results = machine_obj.get_by_regtoken(regtoken, { "registration_token" : regtoken })
                if results.error_code != 0 and len(results.data) != 0:
                    self.logger.debug("regtoken match from machines table")
                    profile_id = results.data[0]["profile_id"]

            # if profile id is still None, check the deployments table
            if profile_id is not None:
                deployment_obj = deployment.Deployment()
                results = deployment_obj.get_by_regtoken(regtoken, { "registration_token" : regtoken })
                if results.error_code != 0 and len(results.data) != 0:
                    self.logger.debug("regtoken match from deployments table")
                    profile_id = results.data[0]["profile_id"]


        if profile_id is None and profile_name != "":
            # no profile ID found for token, try allow a name lookup if specified
            self.logger.debug("passed in profile name is (%s)" % profile_name)
            profile_obj = profile.Profile()
            found_profile = profile_obj.get_by_name({}, { "name" : profile_name })
            if found_profile.error_code == 0 and found_profile.data:
                self.logger.debug("profile assigned from input, given no assignment by token")
                profile_id = found_profile.data["id"]

        self.logger.debug("calling associate with abstract_id: %s", abstract_id)
        self.logger.debug("profile id is: %s", profile_id)
        return abstract_obj.associate(token, abstract_id, machine_id, hostname, ip_addr, mac_addr, profile_id)


methods = Registration()
register_rpc = methods.register_rpc

