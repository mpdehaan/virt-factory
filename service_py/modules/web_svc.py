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

from codes import *

import baseobj
import config_data
import logger

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
        self.dbpath = self.config["databases"]["primary"]
        self.__init_log()
        self.__init_sql()

    def __init_sql(self):
        self.connection = self.sqlite_connect()
        self.cursor = self.connection.cursor()
        
    def __init_log(self):
        # lets see what happens when we c&p the stuff from shadow.py 
        log = logger.Logger()
        self.logger = log.logger
    
    def register_rpc(self, handlers):
        for meth in self.methods:
            print meth
            handlers[meth] = self.methods[meth]

    def sqlite_connect(self):
      """Workaround for \"can't connect to full and/or unicode path\" weirdness"""
      
      current = os.getcwd() 
      os.chdir(os.path.dirname(self.dbpath))
      conn = sqlite.connect(os.path.basename(self.dbpath))
      os.chdir(current)
      return conn 


class AuthWebSvc(WebSvc):

    def __init__(self):
        self.tokens = []
        WebSvc.__init__(self)

    def __validate_foreign_key(self, field_value, field_name, module_instance, null_field_ok=True):
        """
        Used to validate foreign key relationships prior to SQL statements.
        Particularly useful in sqlite, where there are no foreign keys.
        """
        if field is None and null_field_ok:
            return
        try:
            # see if there is an object with this ID.
            module_instance.get({ "id" : field_value})
        except ShadowManagerException:
            raise OrphanedObjectException(comment=field_name,traceback=traceback.format_exc())


    def __get_limit_parms(self, args):
         """
         Extract limit query information from XMLRPC arguments.
         """
         offset = 0
         limit  = 100
         if args.has_key("offset"):
            offset = image_args["offset"]
         if args.has_key("limit"):
            limit = image_args["limit"]
         return (offset, limit) 

    def __simple_list(self, args, need_fields, table_name):
        """
        Shorthand for writing a select * from foo
        """

        (offset, limit) = self.__get_limit_parms(args)
        buf = "SELECT * FROM " + DB_SCHEMA["table"] + " WHERE " + DB_SCHEMA["fields"].join(",") + " LIMIT ?,?"
        results = self.cursor.execute(st, (offset,limit))
        results = self.cursor.fetchall()
 
        if results is None:
             return success()

        data_list = []
        for x in results:
            data_hash = dict(zip(need_fields, result))
            data_list.append(data_hash)

        return success(data)

    def __simple_get(self, args, need_fields, table_name):
        """
        Shorthand for writing a one table select.  
        """
        buf = "SELECT " + DB_SCHEMA["fields"].join(",") + " FROM " + DB_SCHEMA["table"] + " WHERE id=:id"
        self.cursor.execute(buf, { "id" : args["id"] })
        result = self.cursor.fetchone()

        if result is None:
            raise NoSuchObjectException(comment=table_name)

        data_hash = dict(zip(need_fields, result))
        return success(data_hash)

    def __simple_edit(self, args):
        """
        Shorthand for writing an edit statement.
        """
        buf = "UPDATE " + DB_SCHEMA["table"] + " SET "
        for x in DB_SCHEMA["edit"]:
            buf = buf + x + "=:" + x
        buf = buf + " WHERE id=:id"
        self.cursor.execute(buf, args)
        self.connection.commit()
        return success(u.to_datastruct())

    def __simple_add(self, args):
        """
        Shorthand for simple insert.
        """

        buf = "INSERT INTO " + DB_SCHEMA["table"] + "(" + DB_SCHEMA["add"].join(",") + ") "
        labels = [":%s" for entry in DB_SCHEMA["add"]]
        buf = buf + "VALUES (" + labels.join(",") + ")"

        lock = threading.lock()
        lock.acquire() 

        try:
            self.cursor.execute(buf, args)
            self.connection.commit()
        except Exception:
            lock.release()
            raise SQLException(traceback=traceback.format_exc())
         
        rowid = self.cursor.lastrowid
        lock.release()
    
        return success(rowid)

    def __simple_delete(self,args):
        """
        Shorthand for basic delete by id.
        """
        buf = "DELETE FROM " + DB_SCHEMA["table"] + " WHERE id=:id" 
        self.cursor.execute(st, args)
        self.connection.commit()
        return success()

    def token_check(self, token):
        return 1

    # FIXME: not sure if those code make anysense to me. It seems to be
    # an xmlrpc call, and a local method at the same times. That makes my brain hurt
    def token_check_old(self,token):
       """
       Validate that the token passed in to any method call other than user_login
       is correct, and if not, raise an Exception.  Note that all exceptions are
       caught in dispatch, so methods give failing return codes rather than XMLRPCFaults.
       This is a feature, mainly since Rails (and other language bindings) can better
       grok tracebacks this way.
       """

       if not os.path.exists("/var/lib/shadowmanager/settings"):
            x = MisconfiguredException(comment="/var/lib/shadowmanager/settings doesn't exist")
            return x.to_datastruct()

       self.logger.debug("token check")
       now = time.time()
       for t in self.tokens:
           # remove tokens older than 1/2 hour
           if (now - t[1]) > 1800:
               self.tokens.remove(t)
               return TokenExpiredException().to_datastruct()
           if t[0] == token:
               # update the expiration counter
               t[1] = time.time()
               #return SuccessException()
               return success().to_datastruct()
       return TokenInvalidException().to_datastruct()
   
