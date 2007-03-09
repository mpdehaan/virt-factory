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
        # docspath="share/doc/koan-%s/" % VERSION
        manpath  = "share/man/man1/"
#        cobpath  = "/var/lib/cobbler/"
        etcpath  = "/etc/%s" % NAME
        wwwpath  = "/var/www/%s" % NAME
        initpath = "/etc/init.d/"
        logpath  = "/var/log/%s/" % NAME
	settingspath = "/var/lib/%s/" % NAME
        setup(
                name="%s-server" % NAME,
                version = VERSION,
                author = "Michael DeHaan, Adrian Likins, Scott Seago",
                author_email = "et-mgmt-tools@redhat.com",
                url = "http://%s.et.redhat.com/" % NAME,
                license = "GPL",
		scripts = ["scripts/vf_server",
			   "scripts/taskatron",
			   "scripts/vf_import",
			   "scripts/vf_get_puppet_node"],
		package_dir = {"%s" % NAME: "",
			       "%s/server" % NAME: "server",
			       "%s/server/modules" % NAME: "modules/",
			       "%s/server/yaml" % NAME: "yaml/"},
		packages = ["%s" % NAME,
			    "%s/server" % NAME,
			    "%s/server/modules" % NAME,
			    "%s/server/yaml" % NAME],
		#scripts = ["%s/%s" % (NAME, NAME)],
                data_files = [(settingspath, ["settings", "kickstart/kick-fc6.ks"])],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

