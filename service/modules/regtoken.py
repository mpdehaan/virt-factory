#!/usr/bin/python
"""
Virt-factory backend code.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

from server.codes import *
from server import db
from fieldvalidator import FieldValidator

import profile
import machine
import deployment
import web_svc

import os
import threading
import traceback
import base64


class RegToken(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {
             "regtoken_add": self.add,
             "regtoken_delete": self.delete,
             "regtoken_get": self.get,
             "regtoken_get_by_token": self.get_by_token,
             "regtoken_list": self.list
        }
        web_svc.AuthWebSvc.__init__(self)


    def generate(self, token):
         """
         token is base64 encoded short string from /dev/urandom
         """
         fd = open("/dev/urandom")
         data = fd.read(20)
         fd.close()
         data = base64.b64encode(data)
         data = data.replace("=","")
         return data.upper() 


    def add(self, token, args):
        """
        Create a token.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of token attributes.
            - token
            - profile_id (optional)
            - uses_remaining
        @type args: dict
        @raise SQLException: On database error
        """
        required = ('token',)
        optional = ('profile_id', 'uses_remaining')
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_int('uses_remaining')
        session = db.open_session()
        try:
            regtoken = db.RegToken()
            regtoken.update(args)
            session.save(regtoken)
            session.flush()
            return success(regtoken.id)
        finally:
            session.close()


    def delete(self, token, args):
        """
        Delete a token.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of regtoken attributes.
            - id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.RegToken.delete(session, args['id'])
            return success()
        finally:
            session.close()
             
             
    def get_by_token(self, token, args):
        """
        Get all regtokens by token.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of token attributes.
            - token
            - offset (optional)
            - limit (optional)
        @type args: dict
        @return: A list of regtokens.
        @rtype: [dict,]
            - id
            - token
            - profile_id (optional)
            - uses_remaining (optional)
        @raise SQLException: On database error
        """
        required = ('token',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.RegToken)
            tknstr = args['token']
            for rt in query.select_by(token=tknstr, offset=offset, limit=limit):
                result.append(self.expand(rt))
            return success(result)
        finally:
            session.close()


    def list(self, token, args):
        """
        Get all regtokens.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of query attributes.
        @type args: dict
            - offset (optional)
            - limit (optional)
        @return: A list of regtokens.
        @rtype: [dict,]
            - id
            - token
            - profile_id (optional)
            - uses_remaining (optional)
        @raise SQLException: On database error
        """
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for rt in  db.RegToken.list(session, offset, limit):
                result.append(self.expand(rt))
            return success(result)
        finally:
            session.close()


    def check(self, tokenstr):
        """
        Validates a regtoken as being valid. If it fails, raise an
        approriate exception.
        """
        token = None
        session = db.open_session()
        try:
            token = session.query(db.RegToken).selectfirst_by(token=tokenstr)
            if token is None:
                return False
        finally:
             session.close()

        is_specific_token = False

        if token is None:
            
            # no generic regtoken was used, but a new machine or deployment might
            # be using a regtoken by way of kickstart, so those tables must also be checked
            machine = machine.Machine()
            machines = machine.get_by_regtoken(tokenstr, { "registration_token" : tokenstr})
            if len(machines.data) < 0:
                deployment = deployment.Deployment()
                deployments = deployment.get_by_regtoken(tokenstr, { "registration_token" : tokenstr })
                if len(deployments.data) < 0:
                    raise RegTokenInvalidException(comment="regtoken not found in regtoken.check")
                else:
                    is_specific_token = True
            else:
                is_specific_token = True

        if not is_specific_token:
            if token.uses_remaining == 0:
                raise RegTokenExhaustedException(comment="regtoken max uses reached")

            if token.uses_remaining is not None:
                self.__decrement_uses_remaining(token.id, token.uses_remaining)

        # we don't really need to check this, since failure will raise exceptions
        return True
        


    def get(self, token, args):
        """
        Get a regtoken by id.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of token attributes.
            - id
        @type args: dict
        @return: A regtoken.
        @rtype: dict
            - id
            - token
            - profile_id (optional)
            - uses_remaining (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            rt = db.RegToken.get(session, args['id'])
            return success(self.expand(rt))
        finally:
            session.close()


    def expand(self, regtoken):
        result = regtoken.data()
        if regtoken.profile:
            result['profile'] = regtoken.profile.data()
        return result


methods = RegToken()
register_rpc = methods.register_rpc


