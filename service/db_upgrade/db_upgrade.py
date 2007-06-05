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

import re, sys
from subprocess import *

from server import logger
logger.logfilepath = "/var/lib/virt-factory/vf_upgrade_db.log"

import shutil
import string

MIGRATE = "/usr/bin/migrate"
UPGRADE_DIR = "/usr/share/virt-factory/db_schema/upgrade/"
REPOSITORY = "/var/lib/virt-factory/migrate_repository"

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
        self.dbpath = self.config["databases"]["secondary"]

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
        expected_version = 1
        for section in self.upgrade_sections:
            version = int(section[8:])
            if (version != expected_version):
                raise ValueError("error loading upgrades from upgrades.conf. Version " + str(expected_version) + " was not found.")
            files = self.upgrade_config.get(section, "files").split()
            numfiles = len(files)
            for onefile in files:
                pymatch = re.search('.py$', filename)
                if (pymatch and (numfiles > 1)):
                    raise ValueError("invalid upgrade files specified for version " + str(version) + "Only one script allowed for python upgrades.")
                sqlmatch = re.search('-(\w+)-((up|down)grade).sql$', filename)
                if (not (pymatch or sqlmatch)):
                    raise ValueError("invalid upgrade files specified for version " + str(version) + "script " + filename + " must be a python file or a sqlfile in the form upgradename-dbname-(up|down)grade.sql")

            self.versions[version] = section

    def get_loaded_schema_version(self):
        """
        Returns the latest schema version already applied to the database
        """
        return int(self.migrate_cmd("db_version", [self.dbpath, REPOSITORY]))

    def get_repository_schema_version(self):
        """
        Returns the latest schema version committed to the migrate repository
        """
        return int(self.migrate_cmd("version", [REPOSITORY]))

    def get_installed_schema_version(self):
        """
        Returns the latest schema version in the installed package
        """
        return self.versions.keys()[-1]

    def run_upgrades(self):
        """
        Apply each upgrade with a version number greater than the current schema version.
        """
        fs_version = self.get_installed_schema_version()
        db_version = self.get_loaded_schema_version()
        self.commit_versions(true)

        if (fs_version > db_version):
            print "upgrading to version ", fs_version
            output = self.migrate_cmd("upgrade", [self.dbpath, REPOSITORY, version])

    def commit_versions(self, test_first):
        fs_version = self.get_installed_schema_version()
        repo_version = self.get_repository_schema_version()

        for version in self.versions.keys():
            if (version > repo_version):
                print "testing/loading version ", version
                files = self.upgrade_config.get(self.versions[version], "files").split()
                for upgrade_file in files:
                    pymatch = re.search('.py$', filename)
                    sqlmatch = re.search('-(\w+)-((up|down)grade).sql$', filename)
                    
                    tmpfilename = "/tmp/migrate-" + os.path.basename(filename)
                    shutil.copy(filename, tmpfilename)
                    if pymatch:
                        if test_first:
                            output = self.migrate_cmd("test", [tmpfilename, REPOSITORY, self.dbpath])
                        output = self.migrate_cmd("commit", [tmpfilename, REPOSITORY, version])
                    elif sqlmatch:
                        output = self.migrate_cmd("commit", [tmpfilename, REPOSITORY, sqlmatch.group(1), sqlmatch.group(2), version])

    def initialize_schema_version(self):
        """
        Initialize migrate repository and sets the current schema version
        to the latest referenced in upgrades.conf latest entry in upgrades.conf
        """

        # create a new repository
        self.migrate_cmd("create", [REPOSITORY, "virt-factory repository"])
        # add upgrade scripts to repo
        self.commit_versions(false)
        # add the database
        self.migrate_cmd("version_control", [self.dbpath, REPOSITORY, str(self.get_loaded_schema_version())])

    def migrate_cmd(self, command, args):
        """
        Apply schema changes by executing the sql scripts listed in the input file.
        If any scripts result in an error (for sqlite, this is indicated by output
        sent to stdout), log the error output and throw an exception
        """
        cmdline = [MIGRATE, command] + args
        self.logger.info("calling " + cmdline.join(' '))
        
        pipe = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        cmd_output = pipe.stdout.read().strip()
        error_msg = pipe.stderr.read().strip()
        exitCode = pipe.wait()
        if (len(error_msg > 0) or exitCode != 0):
            self.logger.error("error in running " + cmdline)
            self.logger.error(error_msg)
            raise Exception(error_msg)
        else:
            self.logger.info("returned " + cmd_output)
        print cmd_output
        return cmd_output
    
def main(argv):
    """
    Start things up.
    """
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage)
    parser.add_option("-q", "--query",
                  dest="query", type="choice", choices=["d", "db", "r", "repository", "p", "package"], default=None,
                  help="If specified, query schema version of either the database (d,db),  the migrate repository (r,repository) or the installed package (p,package) and exit without attempting an upgrade.")
    parser.add_option("-i", "--initialize",
                  dest="initialize", action="store_true", default=False,
                  help="If specified, initialize the schema version field in the database and exit without attempting an upgrade.")

    (options, args) = parser.parse_args()
    upgrade = Upgrade()
    if (options.query):
        if (options.query in ["d", "db"]):
            print upgrade.get_loaded_schema_version()
        elif  (options.query in ["r", "repository"]):
            print upgrade.get_repository_schema_version()
        elif  (options.query in ["p", "package"]):
            print upgrade.get_installed_schema_version()
    if (options.initialize):
        upgrade.initialize_schema_version()
    if (not (options.query or options.initialize)):
        print "upgrading..."
        upgrade.run_upgrades()



    

if __name__ == "__main__":
    main(sys.argv)


