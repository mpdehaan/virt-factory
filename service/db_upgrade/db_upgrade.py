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
import ConfigParser
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
UPGRADE_DIR = "/usr/share/virt-factory/db_schema/upgrade/"
class Upgrade(object):
    def __init__(self):
        self.__setup_config()
        self.__init_log()
        self.__setup_db()
        self.__setup_upgrade_config()
        
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

    def __setup_upgrade_config(self):
        self.upgrade_config = ConfigParser.ConfigParser()
        self.upgrade_config.read(UPGRADE_DIR + "upgrades.conf")
        self.upgrade_sections = self.upgrade_config.sections()
        self.upgrade_sections.sort()
        self.versions = {}
        for section in self.upgrade_sections:
            self.versions[int(section[8:])] = section

    def sqlite_connect(self):
        """Workaround for \"can't connect to full and/or unicode path\" weirdness"""
        
        current = os.getcwd() 
        os.chdir(os.path.dirname(self.dbpath))
        conn = sqlite.connect(os.path.basename(self.dbpath), isolation_level=None)
        os.chdir(current)
        return conn 

    def get_loaded_schema_version(self):
        schema_obj = schema_version.SchemaVersion()
        current_schema = schema_obj.get_current_version(None)
        if current_schema.data:
            return current_schema.data["version"]
        else:
            return 0

    def get_installed_schema_version(self):
        return self.versions.keys()[-1]

    def run_upgrades(self):
        db_version = self.get_loaded_schema_version()

        for version in self.versions.keys():
            if (version > db_version):
                print "upgrading to version ", version
                self.run_single_upgrade(version, self.versions[version])

    def run_single_upgrade(self, version, section):

        self.start_upgrade(version,
                           self.upgrade_config.get(section, "git_tag"),
                           self.upgrade_config.get(section, "notes"))

        self.apply_changes(version, self.upgrade_config.get(section, "files").split())
        
        self.end_upgrade(version)


    def initialize_schema_version(self):
        if (self.get_loaded_schema_version()):
            raise ValueError("schema version " + str(self.get_loaded_schema_version()) + " is already loaded.")
            
        version = self.get_installed_schema_version()
        section = self.versions[version]
        self.start_upgrade(version,
                           self.upgrade_config.get(section, "git_tag"),
                           self.upgrade_config.get(section, "notes"))
        self.end_upgrade(version)


    def start_upgrade(self, version, git_tag = None, notes = None):
        """
        Mark the upgrade as begun in the db.
        """
        
        args = {}
        args["install_timestamp"] = time.ctime()
        args["version"] = version
        args["git_tag"] = git_tag
        args["notes"] = notes
        args["status"] = SCHEMA_VERSION_BEGIN
        schema_obj = schema_version.SchemaVersion()
        try:
            existing_schema = schema_obj.get_by_version(None, args)
            if existing_schema.data and existing_schema.data["status"]==SCHEMA_VERSION_END:
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
        
    def apply_changes(self, version, sql_script_list):
        """
        Apply schema changes by executing the sql scripts listed in the input file.
        If any scripts result in an error (for sqlite, this is indicated by output
        sent to stdout), log the error output and throw an exception
        """
        self.log("upgrade-begin-" + str(version), UPGRADE_LOG_MESSAGE_INFO)
        for line in sql_script_list:
            sql = line.strip()
            if len(sql) == 0:
                continue
            self.log(sql + "-begin", UPGRADE_LOG_MESSAGE_INFO)
            pipe = os.popen(SQLITE3 + " " + self.dbpath + "  < " + UPGRADE_DIR + sql)
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
                self.log(sql + "-error", UPGRADE_LOG_MESSAGE_ERROR, error_msg)
                raise Exception(error_msg)
            else:
                self.log(sql + "-end", UPGRADE_LOG_MESSAGE_INFO)

        self.log("upgrade-end-" + str(version), UPGRADE_LOG_MESSAGE_INFO)
            
            

    
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
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage)
    parser.add_option("-q", "--query",
                  dest="query", type="choice", choices=["d", "db", "p", "package"], default=None,
                  help="If specified, query schema version of either the database (d,db) or the installed package (p,package) and exit without attempting an upgrade.")
    parser.add_option("-i", "--initialize",
                  dest="initialize", action="store_true", default=False,
                  help="If specified, initialize the schema version field in the database and exit without attempting an upgrade.")

    (options, args) = parser.parse_args()
    upgrade = Upgrade()
    if (options.query):
        if (options.query in ["d", "db"]):
            print upgrade.get_loaded_schema_version()
        elif  (options.query in ["p", "package"]):
            print upgrade.get_installed_schema_version()
    if (options.initialize):
        upgrade.initialize_schema_version()
    if (not (options.query or options.initialize)):
        print "upgrading..."
        upgrade.run_upgrades()



    

if __name__ == "__main__":
    main(sys.argv)


