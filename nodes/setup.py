#!/usr/bin/python

import sys
from distutils.core import setup, Extension
import string

NAME = "virtfactory"
VERSION = "0.0.1"
SHORT_DESC = "%s client server" % NAME
LONG_DESC = """
A small pluggabe xml-rpc used by %s to communicate to individual machines
""" % NAME

if __name__ == "__main__":
        # docspath="share/doc/koan-%s/" % VERSION
        manpath  = "share/man/man1/"
#        cobpath  = "/var/lib/cobbler/"
        etcpath  = "/etc/%s" % NAME
        wwwpath  = "/var/www/%s" % NAME
        initpath = "/etc/init.d/"
        logpath  = "/var/log/%s/" % NAME
        setup(
                name="%s/nodes" % NAME,
                version = VERSION,
                author = "Michael DeHaan, Adrian Likins, Scott Seago",
                author_email = "et-mgmt-tools@redhat.com",
                url = "http://%s.et.redhat.com/" % NAME,
                license = "GPL",
		package_dir = {"nodes": "src", "nodes/modules": "modules/"},
		packages = ["nodes", "nodes/modules"],
		#scripts = ["%s/%s" % (NAME, NAME)],
                data_files = [],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

