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

import logger
import os
import string
import baseobj

class DbUtil(object):
    def __init__(self):
        self.__setup_config()
        self.__init_log()
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

    def __init_log(self):
        # lets see what happens when we c&p the stuff from shadow.py 
        log = logger.Logger()
        self.logger = log.logger

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
            offset = profile_args["offset"]
        if args.has_key("limit"):
            limit = profile_args["limit"]
        return (offset, limit) 

    def filter_param_list(self, full_parameter_list, provided_params):
        """
        Filters the parameter list (full_parameter_list) based on the
        hash of input parameters with values (provided_params). The
        output list includes those parameters in full_parameter_list
        with values provided in provided_params.
        """
        
        return_list = []
        provided_keys = provided_params.keys()
        for param in full_list:
            if param in provided_keys:
                return_list.append(param)
        return return_list

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
               if type(y) == str or type(y) == unicode:
                   y = "'%s'" % y
               self.logger.info( x+y)
               where_parts.append(x + " = " + y)
           where_clause = " WHERE " + string.join(where_parts, " AND ")
        else:
           where_clause = ""         

        buf = "SELECT " + string.join(self.db_schema["fields"], ",") +  " FROM " + self.db_schema["table"]  + " " + where_clause + " LIMIT ?,?"
        self.logger.info( "QUERY: %s" % buf)
        self.logger.info( "OFFSET, LIMIT: %s, %s" % (offset,limit))
        self.cursor.execute(buf, (offset,limit))
        results = self.cursor.fetchall()
        self.logger.info("RESULTS OF QUERY: %s" % results)
 
        if results is None:
             return success([])

        data_list = []
        for x in results:
            data_hash = dict(zip(self.db_schema["fields"], x))
            data_list.append(data_hash)

        self.logger.info("SUCCESS, list=%s" % data_list)

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
        edit_keys = self.filter_param_list(self.db_schema["edit"],args)
        buf = "UPDATE " + self.db_schema["table"] + " SET "
        buf = buf + ", ".join([x + "=:" + x for x in edit_keys])
        buf = buf + " WHERE id=:id"
        self.logger.info("SQL = %s" % buf)
        self.logger.info("ARGS = %s" % args)
        self.cursor.execute(buf, args)
        self.connection.commit()
        return success()  # FIXME: is this what edit should return?

    def simple_add(self, args):
        """
        Shorthand for simple insert.
        """

        add_keys = self.filter_param_list(self.db_schema["add"],args)
        buf = "INSERT INTO " + self.db_schema["table"] + " (" + string.join(add_keys, ',')  + ") "

        # icky...
        labels = [":%s" % entry for entry in add_keys]
        buf = buf + "VALUES (" + string.join(labels, ",") + ")"

        lock = threading.Lock()
        lock.acquire() 

        try:
            self.logger.info("SQL = %s" % buf)
            self.logger.info("ARGS = %s" % args)
            self.cursor.execute(buf, args)
            self.connection.commit()
        except Exception:
            lock.release()
            # temporary...
            (t, v, tb) = sys.exc_info()
            self.logger.debug("Exception occured: %s" % t )
            self.logger.debug("Exception value: %s" % v)
            self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
            raise SQLException(traceback=traceback.format_exc())
         
        rowid = self.cursor.lastrowid
        lock.release()
    
        self.logger.info("SUCCESS, rowid= %s" % rowid)
        return success(rowid)

    def simple_delete(self,args):
        """
        Shorthand for basic delete by id.
        """
        buf = "DELETE FROM " + self.db_schema["table"] + " WHERE id=:id" 
        self.cursor.execute(buf, args)
        self.connection.commit()
        return success()


