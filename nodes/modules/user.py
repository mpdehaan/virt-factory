#!/usr/bin/python

## ShadowManager backend code.
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



from nodes.codes import *

import sys
from modules import web_svc

import os
import base64
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


    def add(self, token, user_args):
         """
         Create a user.  user_args should contain all user fields except ID.
         """
         u = UserData.produce(user_args,OP_ADD)
         # u.id = websvc.get_uid()
         st = """
         INSERT INTO users (username,password,first,middle,last,description,email)
         VALUES (:username,:password,:first,:middle,:last,:description,:email)
         """
         lock = threading.Lock()
         lock.acquire()
         try:
             self.db.cursor.execute(st, u.to_datastruct())
             self.db.connection.commit()
         except Exception:
             lock.release()
             self.db.cursor.close()
             raise
#             raise SQLException(traceback=traceback.format_exc())

         rowid = self.db.cursor.lastrowid
         lock.release()
         self.db.cursor.close()
         return success(rowid)

    def edit(self, token, user_args):
         """
         Edit a user.  user_args should contain all user fields that need to
         be changed.
         """
         # FIXME: allow the password field to NOT be sent, therefore not
         #        changing it.  (OR) just always do XMLRPC/HTTPS and use a 
         #        HTML password field.  Either way.  (We're going to be
         #        wanting HTTPS anyhow).
         u = UserData.produce(user_args,OP_EDIT) # force validation
         st = """
         UPDATE users
         SET password=:password,
         first=:first,
         middle=:middle,
         last=:last,
         description=:description,
         email=:email
         WHERE id=:id
         """
         ds = u.to_datastruct()
         self.db.cursor.execute(st, ds)
         self.db.connection.commit()
         return success(u.to_datastruct())

     # FIXME: don't allow delete if only 1 user left
     # FIXME: consider an undeletable but modifiable admin user

    def delete(self, token, user_args):
         """
         Deletes a user.  The user_args must only contain the id field.
         """
         u = UserData.produce(user_args,OP_DELETE) # force validation
         st = """
         DELETE FROM users WHERE users.id=:id
         """
         self.db.cursor.execute(st, { "id" : u.id })
         self.db.connection.commit()
         # FIXME: failure based on existance
         return success()

    def list(self, token, user_args):
         """
         Return a list of users.  The user_args list is currently *NOT*
         used.  Ideally we need to include LIMIT information here for
         GUI pagination when we start worrying about hundreds of systems.
         """
         # FIXME: limit query support
         offset = 0
         limit  = 100
         if user_args.has_key("offset"):
            offset = user_args["offset"]
         if user_args.has_key("limit"):
            limit = user_args["limit"]
         st = """
         SELECT id,username,password,first,middle,last,description,email FROM users LIMIT ?,?
         """ 
         results = self.db.cursor.execute(st, (offset,limit))
         results = self.db.cursor.fetchall()
         users = []
         for x in results:
             data = {         
                "id"          : x[0],
                "username"    : x[1],
                "password"    : x[2],
                "first"       : x[3],
                "middle"      : x[4],
                "last"        : x[5],
                "description" : x[6],
                "email"       : x[7]
             }
             users.append(UserData.produce(data).to_datastruct(True))
         return success(users)

    def get(self, token, user_args):
         """
         Return a specific user record.  Only the "id" is required in user_args.
         """
         u = UserData.produce(user_args,OP_GET) # force validation
         st = """
         SELECT id,username,password,first,middle,last,description,email from users where users.id=:id
         """
         self.db.cursor.execute(st,{ "id" : u.id })
         x = self.db.cursor.fetchone()
         if x is None:
             raise NoSuchObjectException(comment="user_get")
         data = {
                "id"          : x[0],
                "username"    : x[1],
                "password"    : x[2],
                "first"       : x[3],
                "middle"      : x[4],
                "last"        : x[5],
                "description" : x[6],
                "email"       : x[7]
         }
         return success(UserData.produce(data).to_datastruct(True))

 
methods = User()
register_rpc = methods.register_rpc

