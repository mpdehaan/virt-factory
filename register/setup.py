#!/usr/bin/python

import sys
from distutils.core import setup, Extension
import string
import glob

NAME = "virt-factory"
VERSION = "0.0.1"
SHORT_DESC = "%s registration client" % NAME
LONG_DESC = """
A utility to register machines to the %s server
""" % NAME

if __name__ == "__main__":
        manpath  = "share/man/man1/"
        etcpath  = "/etc/%s" % NAME
        wwwpath  = "/var/www/%s" % NAME
        initpath = "/etc/init.d/"
        logpath  = "/var/log/%s-register/" % NAME
	settingspath = "/var/lib/%s/" % NAME
        setup(
                name="%s-register" % NAME,
                version = VERSION,
                author = "Michael DeHaan, Adrian Likins, Scott Seago",
                author_email = "et-mgmt-tools@redhat.com",
                url = "http://%s.et.redhat.com/" % NAME,
                license = "GPL",
		scripts = ["scripts/vf_register"],
		package_dir = {"%s/register" % NAME: "register"},
		packages = ["%s/register" % NAME],
		data_files = [(logpath, [])],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

