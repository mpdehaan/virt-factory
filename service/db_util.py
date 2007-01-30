#!/usr/bin/python


## ShadowManager backend code.
##
## Copyright 2006, Red Hat, Inc
## Michael DeHaan <mdehaan@redhat.com
## Adrian Likins <alikins@redhat.com
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
##
##

from codes import *
import config_data

import threading
from pysqlite2 import dbapi2 as sqlite

import os
import string
import baseobj

class DbUtil(object):
    def __init__(self):
        self.__setup_config()
        self.__setup_db()

        self.db_schema = None

    def __setup_config(self):
        config_obj = config_data.Config()
        config_result = config_obj.get()
        self.config = config_result

    def __setup_db(self):
        self.dbpath = self.config["databases"]["primary"]
        self.connection = self.sqlite_connect()
        self.cursor = self.connection.cursor()


    def sqlite_connect(self):
        """Workaround for \"can't connect to full and/or unicode path\" weirdness"""
        
        current = os.getcwd() 
        os.chdir(os.path.dirname(self.dbpath))
        conn = sqlite.connect(os.path.basename(self.dbpath), isolation_level=None)
        os.chdir(current)
        return conn 


    def validate_foreign_key(self, field_value, field_name, module_instance, null_field_ok=True):
        """
        Used to validate foreign key relationships prior to SQL statements.
        Particularly useful in sqlite, where there are no foreign keys.
        """
        # FIXME: log instead of print
        # print "validating foreign key %s of %s" % (field_name, field_value)
        if field_value is None and null_field_ok:
            return
        try:
            # see if there is an object with this ID.
            module_instance.get(None, { "id" : field_value})
        except ShadowManagerException:
            raise OrphanedObjectException(comment=field_name,traceback=traceback.format_exc())


    def get_limit_parms(self, args):
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

    # FIXME: is this right? -akl
    def simple_list(self, args, where_args={}):
        """
        Shorthand for writing a select * from foo
        """
        (offset, limit) = self.get_limit_parms(args)

        if len(where_args) > 0:
           where_parts = []
           for x in where_args:
               y = where_args[x]
               if type(y) == str:
                   y = "'%s'" % y
               where_parts.append(x + " = " + y)
           where_clause = " WHERE " + string.join(where_parts, " AND ")
        else:
           where_clause = ""         

        buf = "SELECT " + string.join(self.db_schema["fields"], ",") +  " FROM " + self.db_schema["table"]  + " " + where_clause + " LIMIT ?,?"
        print "QUERY: %s" % buf
        print "OFFSET, LIMIT: %s, %s" % (offset,limit)
        self.cursor.execute(buf, (offset,limit))
        results = self.cursor.fetchall()
        print "RESULTS OF QUERY: %s" % results
 
        if results is None:
             return success([])

        data_list = []
        for x in results:
            data_hash = dict(zip(self.db_schema["fields"], x))
            data_list.append(data_hash)

        # print "SUCCESS, list=%s" % data_list

        base_obj = baseobj.BaseObject()
        return success(base_obj.remove_nulls(data_list))

    def simple_get(self, args):
        """
        Shorthand for writing a one table select.  
        """
        buf = "SELECT " + string.join(self.db_schema["fields"], ',')  + " FROM " + self.db_schema["table"] + " WHERE id=:id"
        self.cursor.execute(buf, { "id" : args["id"] })
        result = self.cursor.fetchone()

        if result is None:
            raise NoSuchObjectException(comment=table_name)

        data_hash = dict(zip(self.db_schema["fields"], result))
        
        base_obj = baseobj.BaseObject()
        return success(base_obj.remove_nulls(data_hash))

    def simple_list_by(self, fieldname, fieldvalue):
        """
        Shorthand for writing a list statement with a WHERE clause.
        """

    def simple_edit(self, args):
        """
        Shorthand for writing an edit statement.
        """
        buf = "UPDATE " + self.db_schema["table"] + " SET "
        for x in self.db_schema["edit"]:
            buf = buf + x + "=:" + x
        buf = buf + " WHERE id=:id"
        self.cursor.execute(buf, args)
        self.connection.commit()
        return success()  # FIXME: is this what edit should return?

    def simple_add(self, args):
        """
        Shorthand for simple insert.
        """

        buf = "INSERT INTO " + self.db_schema["table"] + " (" + string.join(self.db_schema["add"], ',')  + ") "

        # icky...
        labels = [":%s" % entry for entry in self.db_schema["add"]]
        buf = buf + "VALUES (" + string.join(labels, ",") + ")"

        lock = threading.Lock()
        lock.acquire() 

        try:
            print "SQL = %s" % buf
            print "ARGS = %s" % args
            self.cursor.execute(buf, args)
            self.connection.commit()
        except Exception:
            lock.release()
            # temporary...
            traceback.print_exc()
            raise SQLException(traceback=traceback.format_exc())
         
        rowid = self.cursor.lastrowid
        lock.release()
    
        print "SUCCESS, rowid= %s" % rowid
        return success(rowid)

    def simple_delete(self,args):
        """
        Shorthand for basic delete by id.
        """
        buf = "DELETE FROM " + self.db_schema["table"] + " WHERE id=:id" 
        self.cursor.execute(buf, args)
        self.connection.commit()
        return success()

