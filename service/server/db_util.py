#!/usr/bin/python


## Virt-factory backend code.
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
        # lets see what happens when we c&p the stuff from server.py 
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
        except VirtFactoryException:
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
        for param in full_parameter_list:
            if param in provided_keys:
                return_list.append(param)
        return return_list

    # FIXME: is this right? -akl
    def simple_list(self, args, where_args={}, order_by_str = None):
        """
        Shorthand for writing a select * from foo
        """
        return self.nested_list([], args, where_args, order_by_str=order_by_str)

    def nested_get(self, schemas_list, args, where_args={}):
        if not where_args.has_key("id"):  
            # this wasn't called from simple get, thus we need the full table name
            id_key = "%s.id" % self.db_schema["table"]
            where_args[id_key] = args["id"]
        return self.nested_list(schemas_list, args, where_args, return_single=True)

    def nested_list(self, schemas_list, args, where_args={}, return_single=False, allow_none=False, order_by_str = None):
        """
        Select * from foo, with joins on it's nested tables.
        FIXME: outer join support ???
        """
        (offset, limit) = self.get_limit_parms(args)

        if len(where_args) > 0:
           where_parts = []
           for x in where_args:
               y = where_args[x]
               if type(y) == str or type(y) == unicode:
                   y = "%s" % y  # NOTE: users need to escape where_args if needed _before_ passing in
               where_parts.append(str(x) + " = " + str(y))
           where_clause = " WHERE " + string.join(where_parts, " AND ")
        else:
           where_clause = ""

        if ((order_by_str is not None) and len(order_by_str) > 0) :
            order_by_clause = "ORDER BY " + order_by_str
        else:
            order_by_clause = ""

        fields = [] 
        schemas_list.insert(0, self.db_schema)
        for table in schemas_list:
            for field in table["fields"]:
                fields.append("%s.%s" % (table["table"], field))
        fields_clause = ",".join(fields)

        table_names = [ table["table"] for table in schemas_list ]
        table_clause = " FROM " + ",".join(table_names)

        buf = "SELECT " + fields_clause + " " + table_clause + " " + where_clause + order_by_clause + " LIMIT ?,?"
        self.logger.info( "QUERY: %s" % buf)
        self.logger.info( "OFFSET, LIMIT: %s, %s" % (offset,limit))
        self.cursor.execute(buf, (offset,limit))
        results = self.cursor.fetchall()
        self.logger.info("RESULTS OF QUERY: %s" % results)

        if results is None:
            return success([])

        # build the nested confusingness
        result_hash = {}
        result_list = []
        for each_result in results:
            result_hash = {}
            for field, result in zip(fields,each_result):
                (table, real_field) = field.split(".")
                if table.endswith("s"):
                    # tables are plural, the API doesn't want plurals for returns
                    table = table[0:-1]
                if table == schemas_list[0]["table"] or "%ss" % table == schemas_list[0]["table"]:
                    # only nest table results for joined tables
                    if result is not None or allow_none:
                        result_hash[real_field] = result
                else:
                    if not result_hash.has_key(table):
                        result_hash[table] = {}    
                    if result is not None or allow_none:
                        result_hash[table][real_field] = result
            result_list.append(result_hash)
                 
        self.logger.info("SUCCESS, list=%s" % result_list)

        if return_single:
            return success(result_hash)
        else:
            return success(result_list)
        
    def simple_get(self, args):
        """
        Shorthand for writing a one table select.  
        """
        where_args = { "id" : args["id"] }
        return self.nested_get([], args, where_args)

    def simple_edit(self, args):
        """
        Shorthand for writing an edit statement.
        """

        if args["id"] < 0:
            raise NoSuchObjectException()

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
        if args["id"] < 0:
            raise NoSuchObjectException()

        buf = "DELETE FROM " + self.db_schema["table"] + " WHERE id=:id" 
        self.cursor.execute(buf, args)
        self.connection.commit()
        return success()


