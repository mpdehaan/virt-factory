#!/usr/bin/python

import sys
from distutils.core import setup, Extension
import string

NAME = "virt-factory"
VERSION = "0.0.1"
SHORT_DESC = "%s webservicesserver" % NAME
LONG_DESC = """
A small pluggabe xml-rpc daemon used by %s to implement various web services hooks
""" % NAME

if __name__ == "__main__":
        manpath  = "share/man/man1/"
        etcpath  = "/etc/%s" % NAME
        wwwpath  = "/var/www/%s" % NAME
        initpath = "/etc/init.d/"
        logpath  = "/var/log/%s/" % NAME
	settingspath = "/var/lib/%s/" % NAME
	schemapath = "/usr/share/%s/db_schema/" % NAME
	puppetpath = "/usr/share/%s/puppet-config/" % NAME
	manifestpath = "/etc/puppet/manifests/"
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
			   "db/vf_create_db.sh"],
		package_dir = {"%s" % NAME: "",
			       "%s/server" % NAME: "server",
			       "%s/server/modules" % NAME: "modules/",
			       "%s/server/db_upgrade" % NAME: "db_upgrade/",
			       "%s/server/yaml" % NAME: "server/yaml/"},
		packages = ["%s" % NAME,
			    "%s/server" % NAME,
			    "%s/server/modules" % NAME,
			    "%s/server/db_upgrade" % NAME,
			    "%s/server/yaml" % NAME],
                data_files = [(settingspath, ["kickstart/kick-fc6.ks"]),
			      (initpath, ["init-scripts/virt-factory-server"]),
			      (etcpath, ["settings"]),
			      (logpath, []),
			      (schemapath, ["db/schema/schema.sql", 
					    "db/schema/populate.sql"]),
			      (puppetpath, ["puppet-config/puppetmaster", 
					    "puppet-config/puppetd.conf"]),
			      (manifestpath, ["puppet-config/site.pp"])],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

