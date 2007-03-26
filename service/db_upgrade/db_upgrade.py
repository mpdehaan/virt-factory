#!/usr/bin/python
"""
Virt-factory backend code.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>
Adrian Likins <alikins@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

from optparse import OptionParser
from codes import *
import config_data

import os, sys

from server import logger
logger.logfilepath = "/var/lib/virt-factory/vf_upgrade_db.log"
import string
import time
from pysqlite2 import dbapi2 as sqlite

from server.modules import schema_version
from server.modules import upgrade_log_message

SQLITE3 = "/usr/bin/sqlite3"

class Upgrade(object):
    def __init__(self):
        self.__setup_config()
        self.__init_log()
        self.__setup_db()

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

    def start_upgrade(self, version, from_version = None, git_tag = None, notes = None):
        """
        Mark the upgrade as begun in the db.
        """
        
        if (from_version is not None):
            schema_obj = schema_version.SchemaVersion()
            current_schema = schema_obj.get_current_version(None)
            if current_schema.data:
                if (current_schema.data["version"] != from_version):
                    raise ValueError("current schema version is not ", from_version)
            else:
                raise ValueError("schema version ", from_version, " not found.")
        args = {}
        args["install_timestamp"] = time.ctime()
        args["version"] = version
        args["git_tag"] = git_tag
        args["notes"] = notes
        args["status"] = SCHEMA_VERSION_BEGIN
        schema_obj = schema_version.SchemaVersion()
        try:
            existing_schema = schema_obj.get_by_version(None, args)
            if existing_schema.data:
                raise ValueError("schema version ", version, "already exists")
            else:
                self.logger.info( "creating new schema version: version=%i" % version)
                self.logger.info( "creating new schema version: git tag=%s" % git_tag)
                self.logger.info( "creating new schema version: notes=%s"   % notes)
                result = schema_obj.add(None, args)
        except Exception, e:
            (t, v, tb) = sys.exc_info()
            self.logger.debug("Exception occured: %s" % t )
            self.logger.debug("Exception value: %s" % v)
            self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
            raise e

        existing_schema = schema_obj.get_by_version(None, args)

    def log(self, action, message_type, message = None):
        """
        Log upgrade message in the db
        """
        self.logger.info( "schema upgrade, logging action %s" % action)
        self.logger.info( "schema upgrade, message_type %s" % message_type)
        self.logger.info( "schema upgrade, message %s" % message)
        args = {}
        args["action"] = action
        args["message_type"] = message_type
        args["message_timestamp"] = time.ctime()
        if (message is not None):
            args["message"] = message
            
        log_obj = upgrade_log_message.UpgradeLogMessage()
        try:
            result = log_obj.add(None, args)
        except Exception, e:
            (t, v, tb) = sys.exc_info()
            self.logger.debug("Exception occured: %s" % t )
            self.logger.debug("Exception value: %s" % v)
            self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
            raise e
        
    def apply_changes(self, sql_script_list):
        """
        Apply schema changes by executing the sql scripts listed in the input file.
        If any scripts result in an error (for sqlite, this is indicated by output
        sent to stdout), log the error output and throw an exception
        """
        self.log("upgrade-begin", UPGRADE_LOG_MESSAGE_INFO)
        file = open(sql_script_list, 'r')
        for line in file.readlines():
            sql = line.strip()
            if len(sql) == 0:
                continue
            self.log(sql + "-begin", UPGRADE_LOG_MESSAGE_INFO)
            pipe = os.popen(SQLITE3 + " " + self.dbpath + "  < " + sql)
            error_found = 0
            error_msg = ""
            for line in pipe.readlines():
                if len(line.strip()) > 0:
                    error_found = 1
                if (error_found):
                    error_msg = error_msg + line
            closed = pipe.close()
            exitCode = None
            if closed:
                exitCode = os.WIFEXITED(closed) and os.WEXITSTATUS(closed) or 0
            if error_found or exitCode is not None:
                file.close()
                self.log(sql + "-error", UPGRADE_LOG_MESSAGE_ERROR, error_msg)
                raise Exception(error_msg)
            else:
                self.log(sql + "-end", UPGRADE_LOG_MESSAGE_INFO)

        closed = file.close()
        self.log("upgrade-end", UPGRADE_LOG_MESSAGE_INFO)
            
            

    
    def end_upgrade(self, version):
        """
        Mark the upgrade as ended in the db.
        """

        args = {}
        args["version"] = version
        args["status"] = SCHEMA_VERSION_END
        schema_obj = schema_version.SchemaVersion()
        try:
            existing_schema = schema_obj.get_by_version(None, args)
            if existing_schema.data:
                if (existing_schema.data["status"] == SCHEMA_VERSION_BEGIN):
                    args["id"] = existing_schema.data["id"]
                    result = schema_obj.edit(None, args)
                    self.logger.info( "done creating new schema version: version=%i" % version)
                else:
                    raise ValueError("schema version ", version, "status must be 'begin'")
            else:
                raise ValueError("schema version ", version, "does not exist")
        except Exception, e:
            (t, v, tb) = sys.exc_info()
            self.logger.debug("Exception occured: %s" % t )
            self.logger.debug("Exception value: %s" % v)
            self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
            raise e

def main(argv):
    """
    Start things up.
    """
    usage = "usage: %prog [options] new-schema-version file-list"
    parser = OptionParser(usage=usage)
    parser.add_option("-f", "--from-version", dest="from_version",
                      help="Current version (throws an error if the current version differs from this)",
                      default=None)
    parser.add_option("-t", "--git-tag", dest="tag",
                      help="git tag for the checkin which introduces the upgrade",
                      default=None)
    parser.add_option("-n", "--notes", dest="notes",
                      help="notes regarding this upgrade",
                      default=None)
    
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments")    
    print "upgrade to version" + args[0]
    upgrade = Upgrade()
    from_version = options.from_version
    if from_version is not None:
        from_version = int(from_version)

    #mark the upgrade as starting
    upgrade.start_upgrade(int(args[0]), from_version, options.tag, options.notes)

    #apply the sql scripts listed in the passed-in file list
    upgrade.apply_changes(args[1])
    
    #mark the upgrade as done
    upgrade.end_upgrade(int(args[0]))

if __name__ == "__main__":
    main(sys.argv)


