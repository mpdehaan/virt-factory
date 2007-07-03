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

import os, re, sys
from subprocess import *

from server import logger

import shutil
import string

MIGRATE = "/usr/bin/vf_migrate"
UPGRADE_DIR = "/usr/share/virt-factory/db_schema/upgrade/"
REPOSITORY = "/var/lib/virt-factory/db/migrate_repository"

def interpolate_url_password(url):
    if url is None:
        raise SQLException(comment="no connection string specified")
    if url.find("%(password)s") != -1:
        pwfile = open("/etc/virt-factory/db/dbaccess")
        read_pw = pwfile.read()
        pwfile.close()
        url = url % { "password" : read_pw }
    return url

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
        self.dbpath = interpolate_url_password(self.config["databases"]["primary"])

    def __init_log(self):
        # lets see what happens when we c&p the stuff from server.py 
        log = logger.Logger("/var/log/virt-factory/db/vf_upgrade_db.log")
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
                raise ValueError("error loading upgrades from upgrades.conf. Version " + str(expected_version) + " was not found.(" + str(version) + ")")
            files = self.upgrade_config.get(section, "files").split()
            numfiles = len(files)
            for onefile in files:
                pymatch = re.search('.py$', onefile)
                if (pymatch and (numfiles > 1)):
                    raise ValueError("invalid upgrade files specified for version " + str(version) + "Only one script allowed for python upgrades.")
                sqlmatch = re.search('-(\w+)-((up|down)grade).sql$', onefile)
                if (not (pymatch or sqlmatch)):
                    raise ValueError("invalid upgrade files specified for version " + str(version) + "script " + onefile + " must be a python file or a sqlfile in the form upgradename-dbname-(up|down)grade.sql")

            self.versions[version] = section
            expected_version += 1

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

    def run_upgrades(self, version_str = None):
        """
        Apply each upgrade with a version number greater than the current schema version.
        and less than the specified upgrade version
        """
        fs_version = self.get_installed_schema_version()
        db_version = self.get_loaded_schema_version()
        if (version_str):
            new_version = int(version_str)
            if ((new_version > fs_version) or (new_version < db_version)):
                raise ValueError("upgrade version " + str(new_version) +
                                 " must be between " + str(db_version) +
                                 " and " + str(fs_version))
        else:
            new_version = fs_version

        if (new_version > db_version):
            print "upgrading to version ", new_version

        repo_version = self.get_repository_schema_version()
        for version in self.versions.keys():
            if (version > new_version):
                break
            if (version > repo_version):
                print "testing/loading version ", version
                files = self.upgrade_config.get(self.versions[version], "files").split()
                for upgrade_file in files:
                    pymatch = re.search('.py$', upgrade_file)
                    sqlmatch = re.search('-(\w+)-((up|down)grade).sql$', upgrade_file)
                    
                    tmpfilename = "/tmp/migrate-" + os.path.basename(upgrade_file)
                    shutil.copy(UPGRADE_DIR + upgrade_file, tmpfilename)
                    if pymatch:
                        print self.migrate_cmd("test", [tmpfilename, REPOSITORY, self.dbpath])
                        print self.migrate_cmd("commit", [tmpfilename, REPOSITORY, str(version)])
                    elif sqlmatch:
                        print self.migrate_cmd("commit", [tmpfilename, REPOSITORY, sqlmatch.group(1), sqlmatch.group(2), str(version)])

            if (version > db_version):
                print self.migrate_cmd("upgrade", [self.dbpath, REPOSITORY, str(version)])

    def run_downgrades(self, version):
        """
        Downgrade the database to the specified version
        """
        db_version = self.get_loaded_schema_version()
        new_version = int(version)
        if ((new_version > db_version) or (new_version < 0)):
            raise ValueError("downgrade version " + str(new_version) +
                             " must be between 0 and " + str(db_version))
        if (new_version < db_version):
            print "downgrading to version ", new_version
            print self.migrate_cmd("downgrade", [self.dbpath, REPOSITORY, str(new_version)])

    def commit_versions(self):
        fs_version = self.get_installed_schema_version()
        repo_version = self.get_repository_schema_version()

        for version in self.versions.keys():
            if (version > repo_version):
                print "testing/loading version ", version
                files = self.upgrade_config.get(self.versions[version], "files").split()
                for upgrade_file in files:
                    pymatch = re.search('.py$', upgrade_file)
                    sqlmatch = re.search('-(\w+)-((up|down)grade).sql$', upgrade_file)
                    
                    tmpfilename = "/tmp/migrate-" + os.path.basename(upgrade_file)
                    shutil.copy(UPGRADE_DIR + upgrade_file, tmpfilename)
                    if pymatch:
                        print self.migrate_cmd("commit", [tmpfilename, REPOSITORY, str(version)])
                    elif sqlmatch:
                        print self.migrate_cmd("commit", [tmpfilename, REPOSITORY, sqlmatch.group(1), sqlmatch.group(2), str(version)])

    def initialize_schema_version(self):
        """
        Initialize migrate repository and sets the current schema version
        to the latest referenced in upgrades.conf latest entry in upgrades.conf
        """

        # create a new repository
        print self.migrate_cmd("create", [REPOSITORY, "virt-factory repository"])
        # add upgrade scripts to repo
        self.commit_versions()
        # add the database
        print self.migrate_cmd("version_control", [self.dbpath, REPOSITORY, str(self.get_installed_schema_version())])

    def migrate_cmd(self, command, args):
        """
        Apply schema changes by executing the sql scripts listed in the input file.
        If any scripts result in an error (for sqlite, this is indicated by output
        sent to stdout), log the error output and throw an exception
        """
        cmdline = [MIGRATE, command] + args
        self.logger.info("calling " + ' '.join(cmdline))
        
        pipe = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        cmd_output = pipe.stdout.read().strip()
        error_msg = pipe.stderr.read().strip()
        exitCode = pipe.wait()
        if (exitCode != 0):
            self.logger.error("error in running " + ' '.join(cmdline))
            self.logger.error(error_msg)
            raise Exception(error_msg)
        else:
            self.logger.info("returned " + cmd_output)
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
    parser.add_option("-u", "--upgrade",
                  dest="upgrade", default=None,
                  help="Upgrade to a particular schema version")
    parser.add_option("-d", "--downgrade",
                  dest="downgrade",
                  help="Downgrade to a particular schema version")

    (options, args) = parser.parse_args()
    upgrade = Upgrade()

    if (options.query):
        if (options.query in ["d", "db"]):
            print upgrade.get_loaded_schema_version()
        elif  (options.query in ["r", "repository"]):
            # currently printting is done 
            print upgrade.get_repository_schema_version()
        elif  (options.query in ["p", "package"]):
            print upgrade.get_installed_schema_version()
    elif (options.initialize):
        upgrade.initialize_schema_version()
    elif (options.downgrade):
        print "downgrading to version " + options.downgrade
        upgrade.run_downgrades(options.downgrade)
    else:
        if (options.upgrade):
            print "upgrading to version " + options.upgrade
        else:
            print "upgrading to latest version "
        upgrade.run_upgrades(options.upgrade)



    

if __name__ == "__main__":
    main(sys.argv)


