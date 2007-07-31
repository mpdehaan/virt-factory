#!/usr/bin/python

import sys
from distutils.core import setup, Extension
#from setuptools import setup,find_packages
import string
import glob

NAME = "virt-factory"
VERSION = open("version", "r+").read().split()[0]
SHORT_DESC = "%s command line client" % NAME
LONG_DESC = """
A commanline client for controling systems deployed with %s
""" % NAME


if __name__ == "__main__":
 
        manpath    = "share/man/man1/"
        etcpath    = "/etc/%s" % NAME
        logpath    = "/var/log/%s/" % NAME
        logpathdb  = "/var/log/%s/db/" % NAME
        setup(
                name="%s-ampm" % NAME,
                version = VERSION,
                author = "Michael DeHaan, Adrian Likins, Scott Seago",
                author_email = "et-mgmt-tools@redhat.com",
                url = "http://%s.et.redhat.com/" % NAME,
                license = "GPL",
		scripts = ["scripts/ampm",
			   ],
		# package_data = { '' : ['*.*'] },
                package_dir = {"%s/ampm" % NAME: "",
			       "%s/ampm/client" % NAME: "client/",
			       "%s/ampm/command_modules" % NAME: "command_modules/",
			       "%s/ampm/api_modules" % NAME: "api_modules/",
                },
		packages = ["%s/ampm" % NAME,
	        #	    "%s/ampm" % NAME,
			    "%s/ampm/client" % NAME,
	        	    "%s/ampm/api_modules" % NAME,
	  	 	    "%s/ampm/command_modules" % NAME,
			    ],
                data_files = [
			      (logpath, []),
			      (logpathdb, []),
			      ],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

