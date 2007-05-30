#!/usr/bin/python

## Virt-factory backend code.
##
## Copyright 2006, Red Hat, Inc
## Michael DeHaan <mdehaan@redhat.com>
## Scott Seago <sseago@redhat.com>
## Adrian Likins <alikins@redhat.com>
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from server.codes import *
from server import db
from baseobj import FieldValidator

import web_svc

import os
import threading
import time
import traceback


class User(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"user_add": self.add,
                        "user_edit": self.edit,
                        "user_delete": self.delete,
                        "user_list": self.list,
                        "user_get": self.get,}

        web_svc.AuthWebSvc.__init__(self)
        self.__lock = threading.Lock()


    def add(self, token, args):
         """
         Create a user.
         @param args: A dictionary of user attributes.
             - username
             - password
             - first
             - middle (optional)
             - last
             - description
             - email
         @type args: dict
         """
         required = ('username','password', 'first', 'last', 'email')
         optional = ('middle', 'description')
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         self.__lock.acquire()
         try:
             user = db.User()
             user.update(args)
             session.save(user)
             session.flush()
             return success(user.id)
         finally:
             self.__lock.release()
             session.close()


    def edit(self, token, args):
         """
         Edit a user.
         @param args: A dictionary of user attributes.
             - id
             - username (optional)
             - password (optional)
             - first (optional)
             - middle (optional)
             - last (optional)
             - description (optional)
             - email (optional)
         @type args: dict.
         # TODO: password should be stored encrypted.
         """
         required = ('id',)
         optional = ('username','password', 'first', 'middle', 'last', 'email', 'description')
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         self.__lock.acquire()
         try:
             user = db.User.get(session, args['id'])
             user.update(args)
             session.save(user)
             session.flush()
             return success()
         finally:
             self.__lock.release()
             session.close()

    def delete(self, token, args):
         """
         Deletes a user.
         @param args: A dictionary of user attributes.
             - id
         @type args: dict
         """
         required = ('id',)
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         self.__lock.acquire()
         try:
             db.User.delete(session, args['id'])
             return success()
         finally:
             self.__lock.release()
             session.close()


    def list(self, token, args):
         """
         Get all users.
         @param args: A dictionary of user attributes.
         @type args: dict
         @return: A list of users.
         @rtype: [dict,]
             - id
             - username
             - first
             - middle (optional)
             - last
             - description (optional)
             - email
         """
         session = db.open_session()
         try:
             result = []
             offset, limit = self.offset_and_limit(args)
             for user in db.User.list(session, offset, limit):
                 result.append(user.data())
             return success(result)
         finally:
             session.close()

    def get(self, token, args):
         """
         Get a user by id.
         @param args: A dictionary of user attributes.
             - id
         @type args: dict
         """
         required = ('id',)
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         try:
             user = db.User.get(session, args['id'])
             return success(user.data())
         finally:
             session.close()

 
methods = User()
register_rpc = methods.register_rpc


