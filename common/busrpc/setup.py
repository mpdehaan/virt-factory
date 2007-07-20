#!/usr/bin/python

import sys
from distutils.core import setup, Extension
import string
import glob

NAME = "busrpc"
VERSION = open("version", "r+").read().split()[0]
SHORT_DESC = "busprc server and client"
LONG_DESC = """
A rpc implementation that uses dbus and qpid/amqp
"""

if __name__ == "__main__":
        manpath  = "share/man/man1/"
        etcpath  = "/etc/%s" % NAME
        qpidetcpath  = "/etc/qpid"
        wwwpath  = "/var/www/%s" % NAME
        initpath = "/etc/init.d/"
        logpath  = "/var/log/%s/" % NAME
        setup(
                name="%s" % NAME,
                version = VERSION,
                author = "Kevin Smith",
                author_email = "et-mgmt-tools@redhat.com",
                url = "http://%s.et.redhat.com/" % NAME,
                license = "GPL",
		scripts = ["scripts/start-bridge"],
		package_dir = {"busrpc/": "",
			       "busrpc/test/": "test/",},
#			       "busrpc/local/": "local/",
#			       "busrpc/remote/": "remote/",},
		packages = ["busrpc",
			    "busrpc/test",],
#			    "busrpc/local",
#			    "busrpc/remote"],
                data_files = [(etcpath, ["configs/test.conf"]),
			      (qpidetcpath, ["configs/amqp.0-8.xml"]),
			      (logpath, [])],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )


