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

from pysqlite2 import dbapi2 as sqlite

import os
import string

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
        conn = sqlite.connect(os.path.basename(self.dbpath))
        os.chdir(current)
        return conn 


    def validate_foreign_key(self, field_value, field_name, module_instance, null_field_ok=True):
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
    def simple_list(self, args, need_fields, table_name):
        """
        Shorthand for writing a select * from foo
        """
        (offset, limit) = self.get_limit_parms(args)
        buf = "SELECT " + string.join(self.db_schema["fields"], ",") +  " FROM " + self.db_schema["table"]  + " LIMIT ?,?"
        results = self.cursor.execute(buf, (offset,limit))
        results = self.cursor.fetchall()
 
        if results is None:
             return success()

        data_list = []
        for x in results:
            data_hash = dict(zip(need_fields, result))
            data_list.append(data_hash)

        return success(data_list)

    def simple_get(self, args, need_fields, table_name):
        """
        Shorthand for writing a one table select.  
        """
        buf = "SELECT " + string.join(self.db_schema["fields"], ',')  + " FROM " + self.db_schema["table"] + " WHERE id=:id"
        self.cursor.execute(buf, { "id" : args["id"] })
        result = self.cursor.fetchone()

        if result is None:
            raise NoSuchObjectException(comment=table_name)

        data_hash = dict(zip(need_fields, result))
        return success(data_hash)

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
        return success(u.to_datastruct())

    def simple_add(self, args):
        """
        Shorthand for simple insert.
        """

        buf = "INSERT INTO " + self.db_schema["table"] + " (" + string.join(self.db_schema["add"], ',')  + ") "

        # icky...
        labels = [":%s" for entry in self.db_schema["add"]]
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

    def simple_delete(self,args):
        """
        Shorthand for basic delete by id.
        """
        buf = "DELETE FROM " + self.db_schema["table"] + " WHERE id=:id" 
        self.cursor.execute(st, args)
        self.connection.commit()
        return success()

