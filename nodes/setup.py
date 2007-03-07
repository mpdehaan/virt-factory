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
	settingspath = "/var/lib/%s/settings/" % NAME
        setup(
                name="%s/nodes" % NAME,
                version = VERSION,
                author = "Michael DeHaan, Adrian Likins, Scott Seago",
                author_email = "et-mgmt-tools@redhat.com",
                url = "http://%s.et.redhat.com/" % NAME,
                license = "GPL",
		scripts = ["scripts/virtfactory-node"],
		package_dir = {"%s-nodes" % NAME: "src", "%s-nodes/modules" % NAME: "modules/"},
		packages = ["%s-nodes" % NAME, "%s-nodes/modules" % NAME],
		#scripts = ["%s/%s" % (NAME, NAME)],
                data_files = [(settingspath, ["settings"])],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

