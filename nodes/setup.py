#!/usr/bin/python

import sys
from distutils.core import setup, Extension
import string

NAME = "virt-factory"
VERSION = "0.0.1"
SHORT_DESC = "%s client server" % NAME
LONG_DESC = """
A small pluggabe xml-rpc used by %s to communicate to individual machines
""" % NAME

if __name__ == "__main__":
        # docspath="share/doc/koan-%s/" % VERSION
        manpath  = "share/man/man1/"
        etcpath  = "/etc/%s" % NAME
        wwwpath  = "/var/www/%s" % NAME
        initpath = "/etc/init.d/"
        logpath  = "/var/log/%s-nodes/" % NAME
	settingspath = "/etc/%s-nodes/" % NAME
        setup(
                name="%s-nodes" % NAME,
                version = VERSION,
                author = "Michael DeHaan, Adrian Likins, Scott Seago",
                author_email = "et-mgmt-tools@redhat.com",
                url = "http://%s.et.redhat.com/" % NAME,
                license = "GPL",
		scripts = ["scripts/vf_node_server"],
		package_dir = {"%s" % NAME: "",
			       "%s/nodes" % NAME: "nodes",
			       "%s/nodes/modules" % NAME: "modules/",
			       "%s/nodes/yaml" % NAME: "yaml/"},
		packages = ["%s" % NAME,
		            "%s/nodes" % NAME,
			    "%s/nodes/modules" % NAME,
			    "%s/nodes/yaml" % NAME],
                data_files = [(settingspath, ["node-settings"]),
			      (initpath, ["init-scripts/virt-factory-node-server"]),
			      (logpath, [])],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

