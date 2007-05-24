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


    def add(self, token, user_args):
         """
         Create a user.
         @param user_args: A dictionary of user attributes.
             - username
             - password
             - first
             - middle (optional)
             - last
             - description
             - email
         @type user_args: dict
         """
         required = ('username','password', 'first', 'last', 'email')
         optional = ('middle', 'description')
         FieldValidator(user_args).verify_required(required)
         session = db.open_session()
         self.__lock.acquire()
         try:
             user = db.User()
             for key in (required+optional):
                 setattr(user, key, user_args.get(key, None))
             session.save(user)
             session.flush()
             return success(user.id)
         finally:
             self.__lock.release()
             session.close()


    def edit(self, token, user_args):
         """
         Edit a user.
         @param user_args: A dictionary of user attributes.
             - id
             - username (optional)
             - password (optional)
             - first (optional)
             - middle (optional)
             - last (optional)
             - description (optional)
             - email (optional)
         @type user_args: dict.
         # FIXME: don't allow delete if only 1 user left
         # FIXME: consider an undeletable but modifiable admin user
         # FIXME: password should be stored encrypted.
         """
         required = ('id',)
         optional = ('username','password', 'first', 'middle', 'last', 'email', 'description')
         FieldValidator(user_args).verify_required(required)
         session = db.open_session()
         self.__lock.acquire()
         try:
             userid = user_args['id']
             user = session.get(db.User, userid)
             if user is None:
                 raise NoSuchObjectException, userid
             for key in optional:
                 current = getattr(user, key)
                 setattr(user, key, user_args.get(key, current))
             session.save(user)
             session.flush()
             return success(user_args)
         finally:
             self.__lock.release()
             session.close()


    def delete(self, token, user_args):
         """
         Deletes a user.
         @param user_args: A dictionary of user attributes.
             - id
         @type user_args: dict
         """
         required = ('id',)
         FieldValidator(user_args).verify_required(required)
         session = db.open_session()
         self.__lock.acquire()
         try:
             userid = user_args['id']
             user = session.get(db.User, userid)
             if user is None:
                 raise NoSuchObjectException, userid
             if user.username == 'admin':
                 return success()
             session.delete(user)
             session.flush()
             return success()
         finally:
             self.__lock.release()
             session.close()


    def list(self, token, user_args):
         """
         Get all users.
         @param user_args: A dictionary of user attributes.
             - offset (optional)
             - limit (optional default=100)
         @type user_args: dict
         @return: A list of users.
         @rtype: dictionary
             - id
             - username
             - first
             - middle (optional)
             - last
             - description (optional)
             - email
         # FIXME: implement paging
         """
         optional = ('offset', 'limit')
         validator = FieldValidator(user_args)
         validator.verify_int(optional)
         offset = user_args.get(optional[0], 0)
         limit = user_args.get(optional[1], 100)

         session = db.open_session()
         try:
             result = []
             query = session.query(db.User)
             for user in query.select():
                 result.append(self.__userdata(user))
             return success(result)
         finally:
             session.close()

    def get(self, token, user_args):
         """
         Get a user by id.
         @param user_args: A dictionary of user attributes.
             - id
         @type user_args: dict
         """
         required = ('id',)
         validator = FieldValidator(user_args)
         validator.verify_required(required)
         session = db.open_session()
         try:
             userid = user_args['id']
             user = session.get(db.User, userid)
             if user is None:
                 raise NoSuchObjectException(comment=userid)
             return success(self.__userdata(user))
         finally:
             session.close()
     
    def __userdata(self, user):
        result =\
            {'id':user.id,
              'username':user.username,
              'password':user.password,
              'first':user.first,
              'middle':user.middle,
              'last':user.last,
              'description':user.description,
              'email':user.email } 
        return FieldValidator.prune(result)

 
methods = User()
register_rpc = methods.register_rpc


