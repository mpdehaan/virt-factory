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

import baseobj
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
         @param args: A dictionary of token attributes.
             - token
             - profile_id (optional)
             - uses_remaining
         @type args: dict
         """
         required = ('token')
         optional = ('profile_id', 'uses_remaining')
         validator = FieldValidator(args)
         validator.verify_required(required)
         validator.verify_int('uses_remaining')
         session = db.open_session()
         try:
             regtoken = db.RegToken()
             for key in (required+optional):
                 setattr(regtoken, key, args.get(key, None))
             session.save(regtoken)
             session.flush()
             return success(regtoken.id)
         finally:
             session.close()


    def delete(self, token, args):
         """
         Deletes a token.
         @param args: A dictionary of user attributes.
             - id
         @type args: dict
         """
         required = ('id',)
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         try:
             objectid = args['id']
             rt = session.get(db.RegToken, objectid)
             if rt is None:
                 raise NoSuchObjectException(comment=objectid)
             session.delete(rt)
             session.flush()
             return success()
         finally:
             session.close()
             
             
    def get_by_token(self, token, args):
         """
         Get all regtokens by token.
         @param args: A dictionary of token attributes.
             - token
         @type args: dict
         @return: A list of regtokens.
         @rtype: [dict,]
             - id
             - token
             - profile_id (optional)
             - uses_remaining (optional)
         # TODO: nested structures.
         """
         required = ('token',)
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         try:
             result = []
             limit = args.get('limit', 10000)
             offset = args.get('offset', 0)
             query = session.query(db.RegToken)
             for rt in query.select_by(token=args['token'], limit=limit, offset=offset):
                 result.append(rt.data())
             return success(result)
         finally:
             session.close()


    def list(self, token, args):
         """
         Get all regtokens.
         @param args: Not used.
         @type args: dict
         @return: A list of regtokens.
         @rtype: [dict,]
             - id
             - token
             - profile_id (optional)
             - uses_remaining (optional)
         # TODO: nested structures.
         """
         session = db.open_session()
         try:
             result = []
             limit = args.get('limit', 10000)
             offset = args.get('offset', 0)
             for rt in  session.query(db.RegToken).select(limit=limit, offset=offset):
                 result.append(rt.data())
             return success(result)
         finally:
             session.close()


    def check(self, regtoken):
        """
        Validates a regtoken as being valid. If it fails, raise an
        approriate exception.
        """

        st = """
        SELECT
              id, uses_remaining
        FROM
              regtokens
        WHERE
              token=:regtoken
        """

        # FIXME: this really should use the db_util stuff to have one less place
        # to make schema changes.
        self.db.cursor.execute(st, {'regtoken': regtoken})
        x = self.db.cursor.fetchone()

        is_specific_token = False

        if x is None:
            
            # no generic regtoken was used, but a new machine or deployment might
            # be using a regtoken by way of kickstart, so those tables must also be checked
            machine_obj = machine.Machine()
            machines = machine_obj.get_by_regtoken(regtoken, { "registration_token" : regtoken})
            if len(machines.data) < 0:
                deployment_obj = deployment.Deployment()
                deployments = deployment_obj.get_by_regtoken(regtoken, { "registration_token" : regtoken })
                if len(deployments.data) < 0:
                    raise RegTokenInvalidException(comment="regtoken not found in regtoken.check")
                else:
                    is_specific_token = True
            else:
                is_specific_token = True

        if not is_specific_token:
            (id, uses) = x
            if uses == 0:
                raise RegTokenExhaustedException(comment="regtoken max uses reached")

            if uses is not None:
                self.__decrement_uses_remaining(id, uses)

        # we don't really need to check this, since failure will raise exceptions
        return True
        


    def get(self, token, args):
         """
         Get a regtoken by id.
         @param args: A dictionary of token attributes.
             - id
         @type args: dict
         @return: A list of regtokens.
         @rtype: dict
             - id
             - token
             - profile_id (optional)
             - uses_remaining (optional)
         # TODO: nested structures.
         """
         required = ('id',)
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         try:
             result = []
             objectid = args['id']
             rt = session.get(db.RegToken, objectid)
             if rt is None:
                 raise NoSuchObjectException(comment=objectid)
             return success(rt.data())
         finally:
             session.close()



methods = RegToken()
register_rpc = methods.register_rpc


