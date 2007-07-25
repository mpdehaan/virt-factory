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

api = ampmlib.Api(url="http://127.0.0.1/vf/")


from command_modules import list

def print_help():
    print "nothing to see here"
    print


def main():

    print "blip"
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


    if mode not in ["help", "list"]:
        print_help()
        sys.exit()

    modeargs = args[args.index(mode)+1:]
    
    if mode == "list":
        list.run(modeargs)
if __name__ == "__main__":
    main()

  
