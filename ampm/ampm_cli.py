#!/usr/bin/python

# cli tool for accessing virt-factory functionality


# basic modes:
#     status
#     query
#     list
#     migrate
#     pause
#     resume
#     create

import ampmlib


import getopt
import os
import sys

api = ampmlib.Api(url="http://127.0.0.1/vf/",
                  username="admin",
                  password="fedora")


from command_modules import list
from command_modules import query

def print_help():
    print "== This is a useless help string blurb =="
    print


def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv", [
            "help",
            "verbose",
            ])
    except getopt.error, e:
        print _("Error parsing command list arguments: %s") % e
        showHelp() 
        sys.exit(1)

    for (opt, vals) in opts:
        if opt in ["-h", "--help"]:
            print_help()
            sys.exit()
        if opt in ["-v", "--verbose"]:
            verbose = 1

    try:
        mode = args[0]
    except IndexError:
        print_help()
        sys.exit()


    if mode not in ["help", "list", "query"]:
        print_help()
        sys.exit()

    modeargs = args[args.index(mode)+1:]
    
    if mode == "list":
        list.run(modeargs)

    if mode == "query":
        query.run(modeargs)
if __name__ == "__main__":
    main()

  
