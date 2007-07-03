#!/usr/bin/python

import sys
from distutils.core import setup, Extension
import string
import glob

NAME = "virt-factory"
VERSION = open("version", "r+").read().split()[0]
SHORT_DESC = "%s webservicesserver" % NAME
LONG_DESC = """
A small pluggabe xml-rpc daemon used by %s to implement various web services hooks
""" % NAME

if __name__ == "__main__":
        manpath    = "share/man/man1/"
        etcpath    = "/etc/%s" % NAME
        etcpathdb  = "/etc/%s/db" % NAME
        wwwpath    = "/var/www/%s" % NAME
        initpath   = "/etc/init.d/"
        logpath    = "/var/log/%s/" % NAME
        logpathdb  = "/var/log/%s/db/" % NAME
	settingspath = "/var/lib/%s/" % NAME
        migraterepopath = "/var/lib/%s/db/" % NAME
	schemapath = "/usr/share/%s/db_schema/" % NAME
	upgradepath = schemapath + "upgrade/"
	puppetpath = "/usr/share/%s/puppet-config/" % NAME
	manifestpath = "/etc/puppet/manifests/"
	profiletemplatepath = "/usr/share/%s/profile-template/" % NAME
        profilespath    = "/var/lib/%s/profiles/" % NAME
        queuedprofilespath    = "/var/lib/%s/profiles/queued/" % NAME
        setup(
                name="%s-server" % NAME,
                version = VERSION,
                author = "Michael DeHaan, Adrian Likins, Scott Seago",
                author_email = "et-mgmt-tools@redhat.com",
                url = "http://%s.et.redhat.com/" % NAME,
                license = "GPL",
		scripts = ["scripts/vf_server",
			   "scripts/vf_taskatron",
			   "scripts/vf_import",
			   "scripts/vf_nodecomm",
			   "scripts/vf_get_puppet_node",
			   "scripts/vf_upgrade_db",
			   "scripts/vf_config_firewall",
			   "scripts/vf_remove_firewall_rules",
			   "scripts/vf_gen_profile_stub",
			   "db/vf_fix_db_auth",
                           "db/vf_create_db",
                           "scripts/vf_migrate"
                ],
		package_dir = {"%s" % NAME: "",
			       "%s/server" % NAME: "server",
			       "%s/server/modules" % NAME: "modules/",
			       "%s/server/db_upgrade" % NAME: "db_upgrade/",
			       "%s/server/yaml" % NAME: "server/yaml/",
                               "%s/server/migrate" % NAME: "migrate/",
                               "%s/server/migrate/changeset" % NAME: "migrate/changeset/",
                               "%s/server/migrate/changeset/databases" % NAME: "migrate/changeset/databases/",
                               "%s/server/migrate/versioning" % NAME: "migrate/versioning/",
                               "%s/server/migrate/versioning/base" % NAME: "migrate/versioning/base/",
                               "%s/server/migrate/versioning/script" % NAME: "migrate/versioning/script/",
                               "%s/server/migrate/versioning/templates" % NAME: "migrate/versioning/templates/",
                               "%s/server/migrate/versioning/templates/repository" % NAME: "migrate/versioning/templates/repository/",
                               "%s/server/migrate/versioning/templates/repository/default" % NAME: "migrate/versioning/templates/repository/default/",
                               "%s/server/migrate/versioning/templates/repository/default/versions" % NAME: "migrate/versioning/templates/repository/default/versions/",
                               "%s/server/migrate/versioning/templates/script" % NAME: "migrate/versioning/templates/script/"
                },
		packages = ["%s" % NAME,
			    "%s/server" % NAME,
			    "%s/server/modules" % NAME,
			    "%s/server/db_upgrade" % NAME,
			    "%s/server/yaml" % NAME,
                            "%s/server/migrate" % NAME,
                            "%s/server/migrate/changeset" % NAME,
                            "%s/server/migrate/changeset/databases" % NAME,
                            "%s/server/migrate/versioning" % NAME,
                            "%s/server/migrate/versioning/base" % NAME,
                            "%s/server/migrate/versioning/script" % NAME,
                            "%s/server/migrate/versioning/templates" % NAME,
                            "%s/server/migrate/versioning/templates/repository" % NAME,
                            "%s/server/migrate/versioning/templates/repository/default" % NAME,
                            "%s/server/migrate/versioning/templates/repository/default/versions" % NAME,
                            "%s/server/migrate/versioning/script" % NAME
                ],
                data_files = [(settingspath, ["kickstart/kick-fc6.ks"]),
			      (initpath, ["init-scripts/virt-factory-server"]),
			      (etcpath, ["settings"]),
			      (etcpathdb, []),
			      (logpath, []),
			      (logpathdb, []),
			      (migraterepopath, []),
			      (profilespath, []),
			      (queuedprofilespath, []),
			      (upgradepath, ["db/schema/upgrade/upgrades.conf"] + 
					     glob.glob("db/schema/upgrade/*.sql") + 
					     glob.glob("db/schema/upgrade/*.py")),
			      (puppetpath, ["puppet-config/puppetmaster", 
					    "puppet-config/puppet.conf"]),
			      (manifestpath, ["puppet-config/site.pp"]),
			      (profiletemplatepath, ["profile-template/Makefile",
                                                     "profile-template/profile.xml.in",
                                                     "profile-template/vf-profile-template.spec",
                                                     "profile-template/init.pp"])],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

